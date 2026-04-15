import tests.cpu_test as cpu
from enum import Enum
import tests.disks_test as disks
from tests.test_base import TestStatus
import tests.gpu_test as gpu
import tests.network_test as network
import tests.usb_test as usb

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

def gpu_test_runner():
    result = gpu.gpu_test()
    status = ComponentStatus.OK

    if result.status == TestStatus.FAIL:
        status = ComponentStatus.ERROR
    elif result.status == TestStatus.WARN:
        status = ComponentStatus.WARNING
    return {
        "component": "GPU",
        "status": status.value,
        "message": result.message,
        "data": result.data
    }


def network_test_runner():
    result = network.network_test()
    status = ComponentStatus.OK

    if result.status == TestStatus.FAIL:
        status = ComponentStatus.ERROR
    elif result.status == TestStatus.WARN:
        status = ComponentStatus.WARNING

    return {
        "component": "Network",
        "status": status.value,
        "message": result.message,
        "data": result.data,
    }


def usb_test_runner():
    result = usb.usb_test()
    status = ComponentStatus.OK

    if result.status == TestStatus.FAIL:
        status = ComponentStatus.ERROR
    elif result.status == TestStatus.WARN:
        status = ComponentStatus.WARNING

    return {
        "component": "USB",
        "status": status.value,
        "message": result.message,
        "data": result.data,
    }