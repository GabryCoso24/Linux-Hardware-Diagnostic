from typing import Optional, Dict, Any
import psutil
from tests.test_base import TestResult, TestStatus


class NetworkTest:
	"""Diagnostic checks for network interfaces and traffic counters."""

	def __init__(self):
		self._result: Optional[TestResult] = None

	def run(self) -> TestResult:
		if self._result is not None:
			return self._result

		info = self._gather_info()
		self._result = self._evaluate(info)
		return self._result

	def _gather_info(self) -> Dict[str, Any]:
		stats = psutil.net_if_stats()
		counters = psutil.net_io_counters(pernic=True)

		interfaces = []
		for name, st in stats.items():
			if name.startswith(("lo", "docker", "veth", "br-", "virbr", "vmnet")):
				continue

			nic = counters.get(name)
			interfaces.append(
				{
					"name": name,
					"is_up": st.isup,
					"speed_mbps": st.speed,
					"mtu": st.mtu,
					"duplex": int(st.duplex),
					"bytes_sent": nic.bytes_sent if nic else None,
					"bytes_recv": nic.bytes_recv if nic else None,
					"errin": nic.errin if nic else None,
					"errout": nic.errout if nic else None,
					"dropin": nic.dropin if nic else None,
					"dropout": nic.dropout if nic else None,
				}
			)

		return {
			"interfaces": interfaces,
			"interface_count": len(interfaces),
			"up_count": sum(1 for i in interfaces if i["is_up"]),
		}

	def _evaluate(self, info: Dict[str, Any]) -> TestResult:
		if info["interface_count"] == 0:
			return TestResult(
				name="network_test",
				status=TestStatus.FAIL,
				message="No network interfaces detected",
				data=info,
			)

		if info["up_count"] == 0:
			return TestResult(
				name="network_test",
				status=TestStatus.WARN,
				message="No active network interfaces",
				data=info,
			)

		for iface in info["interfaces"]:
			if not iface["is_up"]:
				continue
			errors = (iface.get("errin") or 0) + (iface.get("errout") or 0)
			drops = (iface.get("dropin") or 0) + (iface.get("dropout") or 0)

			if errors > 100:
				return TestResult(
					name="network_test",
					status=TestStatus.WARN,
					message=f"High packet errors detected on {iface['name']}",
					data=info,
				)

			if drops > 100:
				return TestResult(
					name="network_test",
					status=TestStatus.WARN,
					message=f"High packet drops detected on {iface['name']}",
					data=info,
				)

		return TestResult(
			name="network_test",
			status=TestStatus.PASS,
			message="Network interfaces healthy",
			data=info,
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


_test_instance = NetworkTest()


def network_test() -> TestResult:
	return _test_instance.run()


def get_status() -> TestStatus:
	return _test_instance.status


def get_message() -> Optional[str]:
	return _test_instance.message


def get_data() -> Optional[dict]:
	return _test_instance.data

