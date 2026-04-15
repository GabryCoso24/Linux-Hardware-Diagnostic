import time
import os
from datetime import datetime
from tests.test_base import TestResult
import json

class Report:
    def __init__(self, results: list[TestResult] = None):
        self._results: list[TestResult] = results if results is not None else []
    
    def add_result(self, result: TestResult):
        self._results.append(result)
    
    def generate_report(self, results: list[TestResult] = None) -> dict:
        if results is None:
            results = self._results

        lookup = {r.name: r for r in results}
        report_data = {
            "timestamp": time.time(),
            "cpu": self._format_result(result=lookup.get("cpu_test")),
            "disks": self._format_result(result=lookup.get("disks_test")),
            "gpu": self._format_result(result=lookup.get("gpu_test")),
            "network": self._format_result(result=lookup.get("network_test")),
            "usb": self._format_result(result=lookup.get("usb_test")),
        }
        return report_data
    
    def _format_result(self, result: TestResult) -> dict:
        if result is None:
            return {
                "name": "unknown",
                "status": "not_run",
                "message": "Test not executed",
                "data": None
            }
        return {
            "name": result.name,
            "status": result.status.value,
            "message": result.message,
            "data": result.data
        }
    
    def save_report(self, filename: str = None):
        
        self.make_reports_dir()
        
        # Generate filename with timestamp if needed
        if filename is None or filename == 'auto':
            # Auto-generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = f"reports/report_{timestamp}.json"
        elif os.path.sep not in filename and not filename.startswith('reports/'):
            # Only filename provided, add reports/ prefix and timestamp
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            ext = '.' + filename.rsplit('.', 1)[1] if '.' in filename else '.json'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = f"reports/{base_name}_{timestamp}{ext}"
        else:
            # Full path provided, use as-is
            final_path = filename
        
        report_data = self.generate_report()
        with open(final_path, 'w') as f:
            json.dump(report_data, f, indent=4)
        
        return final_path

    def make_reports_dir(self):
        import os
        if not os.path.exists("reports"):
            os.makedirs("reports")
