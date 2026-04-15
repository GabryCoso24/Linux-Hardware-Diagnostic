import os
import time
from typing import Any, Dict, List

import psutil


def human_bytes(value: float) -> str:
    """Convert bytes to a short human-readable representation."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"


def format_uptime(seconds: float) -> str:
    """Format uptime seconds into d hh:mm:ss."""
    total = int(max(0, seconds))
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02}:{minutes:02}:{secs:02}"
    return f"{hours:02}:{minutes:02}:{secs:02}"


class RealtimeMonitor:
    """Collects realtime system metrics suitable for a task-manager style TUI."""

    def __init__(self):
        self._last_net = psutil.net_io_counters()
        self._last_time = time.time()
        self._prime_process_cpu()

    @staticmethod
    def _prime_process_cpu():
        """Prime per-process CPU counters so the next sample has real values."""
        for proc in psutil.process_iter(attrs=[]):
            try:
                proc.cpu_percent(None)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def _network_rates(self) -> Dict[str, float]:
        now = time.time()
        current = psutil.net_io_counters()
        elapsed = max(0.001, now - self._last_time)

        down = max(0.0, current.bytes_recv - self._last_net.bytes_recv) / elapsed
        up = max(0.0, current.bytes_sent - self._last_net.bytes_sent) / elapsed

        self._last_net = current
        self._last_time = now

        return {
            "download_bps": down,
            "upload_bps": up,
            "total_recv": current.bytes_recv,
            "total_sent": current.bytes_sent,
        }

    @staticmethod
    def _top_processes(limit: int = 8) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for proc in psutil.process_iter(attrs=["pid", "name"]):
            try:
                rows.append(
                    {
                        "pid": proc.info["pid"],
                        "name": proc.info.get("name") or "unknown",
                        "cpu_percent": proc.cpu_percent(None),
                        "memory_percent": proc.memory_percent(),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        rows.sort(key=lambda item: (item["cpu_percent"], item["memory_percent"]), reverse=True)
        return rows[: max(1, limit)]

    def snapshot(self, top_n: int = 8) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        sm = psutil.swap_memory()

        disk = None
        try:
            disk = psutil.disk_usage("/")
        except Exception:
            disk = None

        load_avg = None
        if hasattr(os, "getloadavg"):
            try:
                load_avg = os.getloadavg()
            except OSError:
                load_avg = None

        net = self._network_rates()

        return {
            "timestamp": time.time(),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_per_core": psutil.cpu_percent(interval=None, percpu=True),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory": {
                "total": vm.total,
                "used": vm.used,
                "available": vm.available,
                "percent": vm.percent,
            },
            "swap": {
                "total": sm.total,
                "used": sm.used,
                "percent": sm.percent,
            },
            "disk": {
                "total": disk.total if disk else None,
                "used": disk.used if disk else None,
                "free": disk.free if disk else None,
                "percent": disk.percent if disk else None,
            },
            "network": net,
            "load_avg": load_avg,
            "uptime": format_uptime(time.time() - psutil.boot_time()),
            "processes": self._top_processes(top_n),
        }
