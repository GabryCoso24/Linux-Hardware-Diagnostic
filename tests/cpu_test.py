from enum import Enum
import core.system_info as sys_info

class TestResult:
    def __init__(self, name, status, message=None, data=None):
        self.name = name
        self.status = status
        self.message = message
        self.data = data

    def __str__(self):
        return f"TestResult(name={self.name}, status={self.status}, message={self.message}, data={self.data})"
    
    def __repr__(self):
        return self.__str__()


def cpu_test():

    info = {
        "usage" : sys_info.cpu_usage(),
        "cores" : sys_info.core_count()
    }
    
    if info["cores"] <= 0:
        return TestResult(
            "cpu_test",
            "FAIL",
            "No CPU cores detected",
            info
        )

    if info["usage"] > 95:
        return TestResult(
            "cpu_test",
            "WARN",
            "CPU usage extremely high",
            info
        )

    return TestResult(
        "cpu_test",
        "PASS",
        "CPU detected and functioning",
        info
    )