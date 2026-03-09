import json
import subprocess
import psutil

class DiskInfo:
    def __init__(self, mountpoint: str):
        self.mountpoint = mountpoint
        self.usage = self.physical_disk_usage()

    @staticmethod
    def physical_disks():
        """Return only physical block devices found on Linux."""
        result = subprocess.run(
            ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,MODEL,SERIAL,TRAN"],
            capture_output=True,
            text=True,
            check=True,
        )
        devices = json.loads(result.stdout).get("blockdevices", [])

        physical = []
        for dev in devices:
            name = dev.get("name", "")
            if dev.get("type") != "disk":
                continue
            if name.startswith(("loop", "ram", "zram", "dm-")):
                continue

            physical.append(
                {
                    "name": name,
                    "size": dev.get("size"),
                    "model": dev.get("model"),
                    "serial": dev.get("serial"),
                    "transport": dev.get("tran"),
                }
            )

        return physical

    @staticmethod
    def physical_disk_count() -> int:
        return len(DiskInfo.physical_disks())
    
    @staticmethod
    def physical_disk_usage():
        disks = DiskInfo.physical_disks()
        usage_data = []
        for disk in disks:
            mountpoint = f"/dev/{disk['name']}"
            try:
                usage = psutil.disk_usage(mountpoint)
                usage_data.append({
                    "name": disk["name"],
                    "usage": usage
                })
            except Exception:
                continue
        return usage_data
    
    @staticmethod
    def disk_status():
        usage_data = DiskInfo.physical_disk_usage()
        status = []
        for disk in usage_data:
            usage_percent = disk["usage"].percent
            if usage_percent > 95:
                status.append({
                    "name": disk["name"],
                    "status": "error",
                    "message": f"Disk {disk['name']} usage too high: {usage_percent}%",
                    "code": 2
                })
            elif usage_percent > 80:
                status.append({
                    "name": disk["name"],
                    "status": "warning",
                    "message": f"Disk {disk['name']} usage high: {usage_percent}%",
                    "code": 1
                })
            else:
                status.append({
                    "name": disk["name"],
                    "status": "ok",
                    "message": f"Disk {disk['name']} working normally",
                    "code": 0
                })
        return status
    
    def disk_sectors(self):
        try:
            result = subprocess.run(
                ["lsblk", "-J", "-o", "NAME,TYPE,SECTORS"],
                capture_output=True,
                text=True,
                check=True,
            )
            devices = json.loads(result.stdout).get("blockdevices", [])
            for dev in devices:
                if dev.get("name") == self.mountpoint.replace("/dev/", ""):
                    return dev.get("sectors")
        except Exception:
            return None
