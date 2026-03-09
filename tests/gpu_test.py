import shutil
from typing import Optional, Dict, Any

import core.gpu_info as gpu
from tests.test_base import TestResult, TestStatus


class GPUTest:
    def __init__(self):
        self._result: Optional[TestResult] = None

    def run(self) -> TestResult:
        if self._result is not None:
            return self._result

        info = self._gather_info()
        self._result = self._evaluate(info)
        return self._result

    def _gather_info(self) -> Dict[str, Any]:
        gpus = gpu.GPUInfo.detect_gpus_lspci()

        smi_tools = []
        if shutil.which("nvidia-smi"):
            nvidia_gpus = gpu.GPUInfo.detect_nvidia_gpus()
            gpus.extend(nvidia_gpus)
            smi_tools.append("nvidia-smi")
        elif shutil.which("rocm-smi"):
            rocm_gpus = gpu.GPUInfo.detect_rocm_gpus()
            gpus.extend(rocm_gpus)
            smi_tools.append("rocm-smi")

        return {
            "id": len(gpus),  # numero GPU rilevate
            "gpus": gpus,
            "smi_tools": smi_tools,
            f"nvidia_smi": shutil.which("nvidia-smi") is not None,
            "rocm_smi": shutil.which("rocm-smi") is not None,
        }

    def _evaluate(self, info: Dict[str, Any]) -> TestResult:
        if info["id"] == 0:
            return TestResult(
                name="gpu_test",
                status=TestStatus.FAIL,
                message="No GPUs detected",
                data=info,
            )

        vendors = sorted({g.get("vendor", "Altro") for g in info["gpus"]})
        return TestResult(
            name="gpu_test",
            status=TestStatus.PASS,
            message=f"{info['id']} GPU(s) detected ({', '.join(vendors)})",
            data=info,
        )
    
    def invalidate_cache(self):
        """Invalidate cache to force a new test run."""
        self._result = None
    
    @property
    def status(self) -> TestStatus:
        return self.run().status
    
    @property
    def message(self) -> Optional[str]:
        return self.run().message
    
    @property
    def data(self) -> Optional[dict]:
        return self.run().data


# Public API
_test_instance = GPUTest()

def gpu_test() -> TestResult:
    return _test_instance.run()

def get_status() -> TestStatus:
    return _test_instance.status

def get_message() -> Optional[str]:
    return _test_instance.message

def get_data() -> Optional[dict]:
    return _test_instance.data
