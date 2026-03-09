import re
import shutil
import subprocess


class GPUInfo:
    def __init__(self):
        pass
    
    @staticmethod
    def _run(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    @staticmethod
    def _detect_vendor(device_line: str) -> str:
        s = device_line.lower()
        if "nvidia" in s:
            return "NVIDIA"
        if "amd" in s or "advanced micro devices" in s or "ati" in s:
            return "AMD"
        if "intel" in s:
            return "Intel"
        return "Altro"

    @staticmethod
    def _bytes_to_mb(value: str) -> str:
        try:
            return str(int(float(value)) // (1024 * 1024))
        except (ValueError, TypeError):
            return "N/D"

    @staticmethod
    def _print_normalized(title: str, rows: list[dict]):
        if not rows:
            return False

        print(f"\n=== {title} ===")
        for i, r in enumerate(rows, start=1):
            if i > 1:
                print(f"GPU {i}:")
            print(f"  ID: {r.get('id', 'N/D')}")
            print(f"  Nome: {r.get('name', 'N/D')}")
            print(f"  Carico: {r.get('load', 'N/D')}")
            print(f"  VRAM usata: {r.get('mem_used', 'N/D')}")
            print(f"  VRAM totale: {r.get('mem_total', 'N/D')}")
            print(f"  Temperatura: {r.get('temp', 'N/D')}")
            print()
        return True

    @staticmethod
    def detect_gpus_lspci():
        if not shutil.which("lspci"):
            print("lspci non trovato. Installa pciutils: sudo apt install pciutils")
            return []

        out = GPUInfo._run(["lspci"])
        if not out:
            return []

        gpus = []
        pattern = re.compile(
            r"^(?P<pci>\S+)\s+(?P<class>VGA compatible controller|3D controller|Display controller):\s+(?P<name>.+)$",
            re.IGNORECASE,
        )

        for line in out.splitlines():
            m = pattern.match(line.strip())
            if not m:
                continue
            name = m.group("name").strip()
            gpus.append(
                {
                    "pci": m.group("pci"),
                    "class": m.group("class"),
                    "name": name,
                    "vendor": GPUInfo._detect_vendor(name),
                }
            )
        return gpus

    @staticmethod
    def nvidia_info():
        if not shutil.which("nvidia-smi"):
            return False

        cmd = [
            "nvidia-smi",
            "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]
        out = GPUInfo._run(cmd)
        if not out:
            return False

        rows = []
        for line in out.splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) != 6:
                continue
            idx, name, load, mem_used, mem_total, temp = parts
            rows.append(
                {
                    "id": idx,
                    "name": name,
                    "load": f"{load}%",
                    "mem_used": f"{mem_used} MB",
                    "mem_total": f"{mem_total} MB",
                    "temp": f"{temp} °C",
                }
            )

        return GPUInfo._print_normalized("Dettagli NVIDIA", rows)

    @staticmethod
    def amd_info():
        if not shutil.which("rocm-smi"):
            return False

        out = GPUInfo._run(["rocm-smi", "--showproductname", "--showuse", "--showmemuse", "--showtemp"])
        if not out:
            return False

        data = {}
        rx_name = re.compile(r"GPU\[(\d+)\].*?:\s*(?:Card series|Card model|Product Name)\s*:\s*(.+)", re.IGNORECASE)
        rx_load = re.compile(r"GPU\[(\d+)\].*GPU use \(%\)\s*:\s*([0-9.]+)", re.IGNORECASE)
        rx_mem_used = re.compile(r"GPU\[(\d+)\].*VRAM Total Used Memory \(B\)\s*:\s*([0-9.]+)", re.IGNORECASE)
        rx_mem_total = re.compile(r"GPU\[(\d+)\].*VRAM Total Memory \(B\)\s*:\s*([0-9.]+)", re.IGNORECASE)
        rx_temp = re.compile(r"GPU\[(\d+)\].*Temperature.*\(C\)\s*:\s*([0-9.]+)", re.IGNORECASE)

        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue

            m = rx_name.search(line)
            if m:
                idx = m.group(1)
                data.setdefault(idx, {})["name"] = m.group(2).strip()
                continue

            m = rx_load.search(line)
            if m:
                idx = m.group(1)
                data.setdefault(idx, {})["load"] = f"{m.group(2)}%"
                continue

            m = rx_mem_used.search(line)
            if m:
                idx = m.group(1)
                data.setdefault(idx, {})["mem_used"] = f"{GPUInfo._bytes_to_mb(m.group(2))} MB"
                continue

            m = rx_mem_total.search(line)
            if m:
                idx = m.group(1)
                data.setdefault(idx, {})["mem_total"] = f"{GPUInfo._bytes_to_mb(m.group(2))} MB"
                continue

            m = rx_temp.search(line)
            if m:
                idx = m.group(1)
                data.setdefault(idx, {})["temp"] = f"{m.group(2)} °C"
                continue

        rows = []
        for idx in sorted(data.keys(), key=lambda x: int(x)):
            d = data[idx]
            rows.append(
                {
                    "id": idx,
                    "name": d.get("name", "AMD GPU"),
                    "load": d.get("load", "N/D"),
                    "mem_used": d.get("mem_used", "N/D"),
                    "mem_total": d.get("mem_total", "N/D"),
                    "temp": d.get("temp", "N/D"),
                }
            )

        if rows:
            return GPUInfo._print_normalized("Dettagli AMD", rows)

        # fallback se formato rocm-smi cambia
        print("\n=== Dettagli AMD ===")
        print(out.strip())
        return True

    @staticmethod
    def intel_info(gpus):
        intel_gpus = [g for g in gpus if g["vendor"] == "Intel"]
        if not intel_gpus:
            return False

        rows = []
        for i, g in enumerate(intel_gpus):
            rows.append(
                {
                    "id": g["pci"],
                    "name": g["name"],
                    "load": "N/D",
                    "mem_used": "N/D",
                    "mem_total": "N/D",
                    "temp": "N/D",
                }
            )

        GPUInfo._print_normalized("Dettagli Intel (base)", rows)
        print("Per metriche live Intel puoi usare: intel_gpu_top")
        return True

    @staticmethod
    def gpu_info():
        gpus = GPUInfo.detect_gpus_lspci()
        if not gpus:
            print("Nessuna GPU rilevata.")
            return

        print(f"=== GPU rilevate: {len(gpus)} ===")
        for i, g in enumerate(gpus, start=1):
            if i > 1:
                print(f"GPU {i}:")
            print(f"  PCI: {g['pci']}")
            print(f"  Classe: {g['class']}")
            print(f"  Vendor: {g['vendor']}")
            print(f"  Nome: {g['name']}")
            print()

        GPUInfo.nvidia_info()
        GPUInfo.amd_info()
        GPUInfo.intel_info(gpus)


if __name__ == "__main__":
    GPUInfo.gpu_info()