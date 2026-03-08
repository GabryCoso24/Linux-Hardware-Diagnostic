import tests.cpu_test as cpu
from enum import Enum

class ComponentStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"

def cpu_test_runner():
    print(cpu.cpu_test())