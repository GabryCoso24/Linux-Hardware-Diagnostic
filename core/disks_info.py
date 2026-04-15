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
        """Return usage by physical disk mapped through mounted partitions."""
        partitions = psutil.disk_partitions(all=False)
        usage_data = []

        for disk in DiskInfo.physical_disks():
            base_dev = f"/dev/{disk['name']}"
            matching_mounts = [
                p.mountpoint
                for p in partitions
                if p.device == base_dev or p.device.startswith(base_dev)
            ]

            if not matching_mounts:
                continue

            highest = None
            for mountpoint in matching_mounts:
                try:
                    usage = psutil.disk_usage(mountpoint)
                except Exception:
                    continue

                if highest is None or usage.percent > highest["usage"].percent:
                    highest = {
                        "name": disk["name"],
                        "mountpoint": mountpoint,
                        "usage": usage,
                    }

            if highest is not None:
                usage_data.append(highest)

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

    @staticmethod
    def physical_disk_sectors():
        """Return sector information for each physical disk."""
        try:
            result = subprocess.run(
                ["lsblk", "-b", "-J", "-o", "NAME,TYPE,SIZE,PHY-SEC,LOG-SEC,SECTORS"],
                capture_output=True,
                text=True,
                check=True,
            )
            devices = json.loads(result.stdout).get("blockdevices", [])
        except Exception:
            return []

        sectors = []
        for dev in devices:
            name = dev.get("name", "")
            if dev.get("type") != "disk":
                continue
            if name.startswith(("loop", "ram", "zram", "dm-")):
                continue

            sectors.append(
                {
                    "name": name,
                    "size_bytes": DiskInfo._safe_int(dev.get("size")),
                    "physical_sector": DiskInfo._safe_int(dev.get("phy-sec")),
                    "logical_sector": DiskInfo._safe_int(dev.get("log-sec")),
                    "sectors": DiskInfo._safe_int(dev.get("sectors")),
                }
            )

        return sectors

    @staticmethod
    def disk_sector_status():
        """Evaluate whether sector metadata is coherent for physical disks."""
        statuses = []
        for entry in DiskInfo.physical_disk_sectors():
            name = entry["name"]
            psec = entry.get("physical_sector")
            lsec = entry.get("logical_sector")
            count = entry.get("sectors")

            if not psec or not lsec or not count:
                statuses.append(
                    {
                        "name": name,
                        "status": "warning",
                        "message": f"Disk {name} sector metadata unavailable",
                        "code": 1,
                    }
                )
                continue

            if psec <= 0 or lsec <= 0 or count <= 0:
                statuses.append(
                    {
                        "name": name,
                        "status": "error",
                        "message": f"Disk {name} has invalid sector values",
                        "code": 2,
                    }
                )
                continue

            if psec % lsec != 0:
                statuses.append(
                    {
                        "name": name,
                        "status": "warning",
                        "message": f"Disk {name} reports non-aligned physical/logical sectors",
                        "code": 1,
                    }
                )
                continue

            statuses.append(
                {
                    "name": name,
                    "status": "ok",
                    "message": f"Disk {name} sector layout coherent",
                    "code": 0,
                }
            )

        return statuses

    @staticmethod
    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    