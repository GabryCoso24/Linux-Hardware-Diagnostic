from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class TestStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class TestResult:
    """Result of a hardware test."""
    name: str
    status: TestStatus
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def is_passing(self) -> bool:
        return self.status == TestStatus.PASS
    
    def is_warning(self) -> bool:
        return self.status == TestStatus.WARN
    
    def is_failing(self) -> bool:
        return self.status == TestStatus.FAIL