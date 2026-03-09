from typing import Optional, Dict, Any
import core.cpu_info as cpu_info
from tests.test_base import TestResult, TestStatus


class CPUTest:
    """Comprehensive diagnostic test for the CPU."""
    
    def __init__(self):
        self._result: Optional[TestResult] = None
    
    def run(self) -> TestResult:
        """Run the CPU test and return the cached result."""
        if self._result is not None:
            return self._result
        
        info = self._gather_info()
        self._result = self._evaluate(info)
        return self._result
    
    def _gather_info(self) -> Dict[str, Any]:
        """Collect all CPU metrics used by the test."""
        return {
            "cores": cpu_info.core_count(),
            "usage": cpu_info.cpu_usage(),
            "core_usage": cpu_info.core_usage(),
            "frequency": cpu_info.cpu_freq(),
            "status": cpu_info.cpu_status(),
            "temperature": cpu_info.cpu_temperature()
        }
    
    def _evaluate(self, info: dict) -> TestResult:
        """Evaluate collected metrics and produce a test result."""
        
        # Test 1: Verify CPU presence.
        if info["cores"] <= 0:
            return TestResult(
                name="cpu_test",
                status=TestStatus.FAIL,
                message="No CPU cores detected",
                data=info
            )
        
        # Test 2: Reuse existing cpu_status() evaluation.
        cpu_status = info["status"]
        
        if cpu_status["code"] == 2:  # Error
            return TestResult(
                name="cpu_test",
                status=TestStatus.FAIL,
                message=cpu_status["message"],
                data=info
            )
        
        if cpu_status["code"] == 1:  # Warning (overclocked or high usage)
            return TestResult(
                name="cpu_test",
                status=TestStatus.WARN,
                message=cpu_status["message"],
                data=info
            )
        
        # Test 3: Detect inactive cores under non-idle load.
        dead_cores = [
            core for core in info["core_usage"] 
            if core["usage"] == 0 and info["usage"] > 10
        ]
        
        if dead_cores:
            return TestResult(
                name="cpu_test",
                status=TestStatus.WARN,
                message=f"{len(dead_cores)} core(s) appear inactive",
                data=info
            )
        
        # Test 4: Detect unusually low frequency (possible throttling).
        freq = info["frequency"]
        if freq["current_mhz"] < freq["min"] * 0.5:
            return TestResult(
                name="cpu_test",
                status=TestStatus.WARN,
                message="CPU frequency unusually low (possible throttling)",
                data=info
            )
        
        # Test 5: Check temperature thresholds.
        if "temperature" in info and info["temperature"]:
            if info["temperature"] > 90:
                return TestResult(
                    name="cpu_test",
                    status=TestStatus.FAIL,
                    message=f"CPU temperature critical: {info['temperature']}°C",
                    data=info
                )
            elif info["temperature"] > 80:
                return TestResult(
                    name="cpu_test",
                    status=TestStatus.WARN,
                    message=f"CPU temperature high: {info['temperature']}°C",
                    data=info
                )
        
        # All checks passed.
        return TestResult(
            name="cpu_test",
            status=TestStatus.PASS,
            message=cpu_status["message"],
            data=info
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
_test_instance = CPUTest()

def cpu_test() -> TestResult:
    return _test_instance.run()

def get_status() -> TestStatus:
    return _test_instance.status

def get_message() -> Optional[str]:
    return _test_instance.message

def get_data() -> Optional[dict]:
    return _test_instance.data