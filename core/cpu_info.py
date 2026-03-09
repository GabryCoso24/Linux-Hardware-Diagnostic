import psutil
from enum import Enum
import cpuinfo

class CPUInfo:
    def __init__(self):
        self.info = cpuinfo.get_cpu_info()
        self.model = self.info['brand_raw']
        self.vendor = self.info['vendor_id_raw']
        self.architecture = self.info['arch_string_raw']
        self.threads = psutil.cpu_count(logical=True)
        self.load_avg = psutil.getloadavg()
        self.temperature = self.cpu_temperature()

    @staticmethod
    def cpu_temperature():
        """Return CPU temperature in Celsius or None if unavailable."""
        try:
            temps = psutil.sensors_temperatures()
        except (AttributeError, OSError):
            return None

        if not temps:
            return None

        for sensor_name in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
            entries = temps.get(sensor_name)
            if entries:
                current = entries[0].current
                if current is not None:
                    return current

        # Fallback: first available sensor entry with a current value.
        for entries in temps.values():
            if entries and entries[0].current is not None:
                return entries[0].current

        return None

    @staticmethod
    def cpu_usage():
        # Get the current CPU usage percentage
        cpu_usage = psutil.cpu_percent(interval=1)
        return cpu_usage  # CPU usage percentage.

    @staticmethod
    def core_count():
        # Get the number of CPU cores
        cpu_cores = psutil.cpu_count(logical=True)

        return cpu_cores  # Number of logical CPU cores.

    @staticmethod
    def core_usage():
        per_cpu = psutil.cpu_percent(interval=1, percpu=True)
        cores = []

        for core_id, usage in enumerate(per_cpu):
            cores.append({
                "core_id": core_id,
                "usage": usage
            })

        return cores

    @staticmethod
    def cpu_status():
        usage = CPUInfo.cpu_usage()
        freq = psutil.cpu_freq()

        status = {}
        
        if usage > 95:
            status = {
                "status": "error",
                "message": f"CPU usage too high: {usage}%",
                "code": 2
            }
        elif freq.current > freq.max * 1.05:
            status = {
                "status": "overclocked",
                "message": f"CPU running above max frequency",
                "code": 1
            }
        elif usage > 80:
            status = {
                "status": "warning",
                "message": f"CPU usage high: {usage}%",
                "code": 1
            }
        else: 
            status = {
                "status": "ok",
                "message": "CPU working normally",
                "code": 0
            }
        
        return status

    @staticmethod
    def cpu_freq():
        """Returns CPU frequency info as dictionary"""
        freq = psutil.cpu_freq()
        return {
            "current_mhz": freq.current,  # Current frequency in MHz, e.g. 2400.0.
            "min": freq.min,  # Minimum frequency in MHz, e.g. 800.0.
            "max": freq.max,  # Maximum frequency in MHz, e.g. 3200.0.
            "current_ghz": freq.current / 1000,  # Current frequency in GHz, e.g. 2.4.
        }

    @staticmethod
    def get_info():
        info = cpuinfo.get_cpu_info()
        model = info['brand_raw']
        vendor = info['vendor_id_raw']
        architecture = info['arch_string_raw']
        threads = psutil.cpu_count(logical=True)
        load_avg = psutil.getloadavg() 
        cpu_temp = CPUInfo.cpu_temperature()

        print(f"{vendor} {model} {architecture} {threads} {load_avg} {cpu_temp}")
