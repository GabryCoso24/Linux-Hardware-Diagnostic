import psutil
from enum import Enum
import cpuinfo

def cpu_usage():
    # Get the current CPU usage percentage
    cpu_usage = psutil.cpu_percent(interval=1)
    return cpu_usage #cpu percentage usage

def core_count():
    # Get the number of CPU cores
    cpu_cores = psutil.cpu_count(logical=True)

    return cpu_cores #number of cpu cores

def core_usage():
    per_cpu = psutil.cpu_percent(interval=1, percpu=True)
    cores = []

    for core_id, usage in enumerate(per_cpu):
        cores.append({
            "core_id": core_id,
            "usage": usage
        })

    return cores

def cpu_status():
    usage = cpu_usage()
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

def cpu_freq():
    """Returns CPU frequency info as dictionary"""
    freq = psutil.cpu_freq()
    return {
        "current_mhz": freq.current,     # current frequency in MHz, Es: 2400.0
        "min": freq.min,              # minimum frequency in MHz, Es: 800.0
        "max": freq.max,              # maximum frequency in MHz, Es: 3200.0
        "current_ghz": freq.current / 1000  # current frequency in GHz, Es: 2.4
    }

def get_info():
    info = cpuinfo.get_cpu_info()
    model = info['brand_raw']
    vendor = info['vendor_id_raw']
    architecture = info['arch_string_raw']
    threads = psutil.cpu_count(logical=True)
    load_avg = psutil.getloadavg() 
    cpu_temp = None
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            cpu_temp = temps['coretemp'][0].current
        elif 'k10temp' in temps:
            cpu_temp = temps['k10temp'][0].current
    except (AttributeError, KeyError):
        pass

    print(f"{vendor} {model} {architecture} {threads} {load_avg} {cpu_temp}")
