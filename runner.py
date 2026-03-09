import tests.cpu_test as cpu
from enum import Enum
import tests.disks_test as disks
from tests.test_base import TestStatus

class ComponentStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"

def cpu_test_runner():
    result = cpu.cpu_test()
    status = ComponentStatus.OK

    if result.status == TestStatus.FAIL:
        status = ComponentStatus.ERROR
    elif result.status == TestStatus.WARN:
        status = ComponentStatus.WARNING

    return {
        "component": "CPU",
        "status": status.value,
        "message": result.message,
        "data": result.data
    }


def disks_test_runner():
    result = disks.disks_test()
    status = ComponentStatus.OK

    if result.status == TestStatus.FAIL:
        status = ComponentStatus.ERROR
    elif result.status == TestStatus.WARN:
        status = ComponentStatus.WARNING

    return {
        "component": "Disks",
        "status": status.value,
        "message": result.message,
        "data": result.data
    }

def generate_report():
    report = {
        "cpu": cpu_test_runner(),
        "disks": disks_test_runner()
    }
    return report