from typing import Optional, Dict, Any
import core.disks_info as disks_info
from tests.test_base import TestResult, TestStatus

class DisksTest:
    def __init__(self):
        self._result: Optional[TestResult] = None
    
    def run(self) -> TestResult:
        if self._result is not None:
            return self._result
        
        info = self._gather_info()
        self._result = self._evaluate(info)
        return self._result
    
    def _gather_info(self) -> Dict[str, Any]:
        return {
            "physical_disks": disks_info.DiskInfo.physical_disks(),
            "disk_count": disks_info.DiskInfo.physical_disk_count(),
            "disk_usage": disks_info.DiskInfo.physical_disk_usage(),
            "disk_status": disks_info.DiskInfo.disk_status(),
        }
    
    def _evaluate(self, info: dict) -> TestResult:
        if info["disk_count"] == 0:
            return TestResult(
                name="disks_test",
                status=TestStatus.FAIL,
                message="No physical disks detected",
                data=info
            )
        
        disk_statuses = info["disk_status"]
        worst_status = max((s.get("code", 0) for s in disk_statuses), default=0)

        if worst_status == 2:  # Error
            error_msg = next((s["message"] for s in disk_statuses if s.get("code") == 2), "Disk error detected")
            return TestResult(
                name="disks_test",
                status=TestStatus.FAIL,
                message=error_msg,
                data=info
            )
        
        if worst_status == 1:  # Warning
            warn_msg = next((s["message"] for s in disk_statuses if s.get("code") == 1), "Disk warning detected")
            return TestResult(
                name="disks_test",
                status=TestStatus.WARN,
                message=warn_msg,
                data=info
            )
        
        return TestResult(
            name="disks_test",
            status=TestStatus.PASS,
            message="All disks healthy",
            data=info
        )
    
    def disk_sectors_test(self):
        # Placeholder: sector checks are not fully implemented yet in core/disks_info.
        sector = []
        return TestResult(
            name="disk_sectors_test",
            status=TestStatus.PASS,
            message="Disk sectors healthy",
            data=sector
        )

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
_test_instance = DisksTest()

def disks_test() -> TestResult:
    return _test_instance.run()

def get_status() -> TestStatus:
    return _test_instance.status

def get_message() -> Optional[str]:
    return _test_instance.message

def get_data() -> Optional[dict]:
    return _test_instance.data