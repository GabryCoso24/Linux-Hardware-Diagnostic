import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from tests.test_base import TestResult, TestStatus


class USBTest:
	"""Diagnostic checks for connected USB devices."""

	def __init__(self):
		self._result: Optional[TestResult] = None

	def run(self) -> TestResult:
		if self._result is not None:
			return self._result

		info = self._gather_info()
		self._result = self._evaluate(info)
		return self._result

	def _gather_info(self) -> Dict[str, Any]:
		devices = self._list_usb_devices()
		return {
			"devices": devices,
			"device_count": len(devices),
			"lsusb_available": shutil.which("lsusb") is not None,
		}

	def _evaluate(self, info: Dict[str, Any]) -> TestResult:
		if info["device_count"] == 0:
			return TestResult(
				name="usb_test",
				status=TestStatus.WARN,
				message="No USB devices detected",
				data=info,
			)

		repeated = self._detect_duplicate_addresses(info["devices"])
		if repeated:
			return TestResult(
				name="usb_test",
				status=TestStatus.WARN,
				message="Duplicate USB bus/device entries detected",
				data={**info, "duplicates": sorted(repeated)},
			)

		return TestResult(
			name="usb_test",
			status=TestStatus.PASS,
			message=f"{info['device_count']} USB device(s) detected",
			data=info,
		)

	def _list_usb_devices(self):
		devices = self._lsusb_devices()
		if devices:
			return devices
		return self._sysfs_usb_devices()

	@staticmethod
	def _lsusb_devices():
		if not shutil.which("lsusb"):
			return []

		try:
			result = subprocess.run(
				["lsusb"],
				capture_output=True,
				text=True,
				check=True,
			)
		except (subprocess.CalledProcessError, FileNotFoundError):
			return []

		devices = []
		pattern = re.compile(
			r"^Bus\s+(?P<bus>\d+)\s+Device\s+(?P<dev>\d+):\s+ID\s+(?P<id>[0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s*(?P<desc>.*)$"
		)
		for line in result.stdout.splitlines():
			m = pattern.match(line.strip())
			if not m:
				continue
			devices.append(
				{
					"bus": m.group("bus"),
					"device": m.group("dev"),
					"id": m.group("id"),
					"description": m.group("desc") or "Unknown",
				}
			)
		return devices

	@staticmethod
	def _sysfs_usb_devices():
		root = Path("/sys/bus/usb/devices")
		if not root.exists():
			return []

		devices = []
		for dev in root.iterdir():
			if not dev.is_dir():
				continue
			busnum = USBTest._read_text(dev / "busnum")
			devnum = USBTest._read_text(dev / "devnum")
			vid = USBTest._read_text(dev / "idVendor")
			pid = USBTest._read_text(dev / "idProduct")

			if not busnum or not devnum or not vid or not pid:
				continue

			manufacturer = USBTest._read_text(dev / "manufacturer") or "Unknown"
			product = USBTest._read_text(dev / "product") or "Unknown"
			devices.append(
				{
					"bus": busnum.zfill(3),
					"device": devnum.zfill(3),
					"id": f"{vid}:{pid}",
					"description": f"{manufacturer} {product}".strip(),
				}
			)
		return devices

	@staticmethod
	def _read_text(path: Path) -> Optional[str]:
		try:
			return path.read_text(encoding="utf-8").strip()
		except OSError:
			return None

	@staticmethod
	def _detect_duplicate_addresses(devices):
		seen = set()
		duplicates = set()
		for d in devices:
			key = (d.get("bus"), d.get("device"))
			if key in seen:
				duplicates.add(f"{key[0]}:{key[1]}")
			seen.add(key)
		return duplicates

	@property
	def status(self) -> TestStatus:
		return self.run().status

	@property
	def message(self) -> Optional[str]:
		return self.run().message

	@property
	def data(self) -> Optional[dict]:
		return self.run().data


_test_instance = USBTest()


def usb_test() -> TestResult:
	return _test_instance.run()


def get_status() -> TestStatus:
	return _test_instance.status


def get_message() -> Optional[str]:
	return _test_instance.message


def get_data() -> Optional[dict]:
	return _test_instance.data

