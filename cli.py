import runner
import pprint
import argparse as ap
import core.report as report_gen
import tests.cpu_test as cpu_test
import tests.disks_test as disks_test
import tests.gpu_test as gpu_test
import tests.network_test as network_test
import tests.usb_test as usb_test
import tui

parser = ap.ArgumentParser(description="Hardware Diagnostic Tool")
parser.add_argument("--cpu", action="store_true", help="Run CPU test")
parser.add_argument("--disks", action="store_true", help="Run Disks test")
parser.add_argument("--gpu", action="store_true", help="Run GPU test")
parser.add_argument("--network", action="store_true", help="Run Network test")
parser.add_argument("--usb", action="store_true", help="Run USB test")
parser.add_argument("--all", action="store_true", help="Run all tests")
parser.add_argument("--report", nargs='?', const='auto', help="Save report to file (optional: specify filename or leave empty for auto-generated name)")
parser.add_argument("--tui", action="store_true", help="Run interactive TUI")
parser.add_argument("--monitor", action="store_true", help="Run realtime resource monitor")


def _print_result(result: dict):
   print(f"{result['component']} Test Result:", result["status"])
   print(f"{result['component']} Test Message:", result["message"])
   print(f"{result['component']} Test Data:")
   pprint.pprint(result["data"])


def _run_all_runners():
   return [
      runner.cpu_test_runner(),
      runner.disks_test_runner(),
      runner.gpu_test_runner(),
      runner.network_test_runner(),
      runner.usb_test_runner(),
   ]


def _build_report(path: str):
   report = report_gen.Report()
   report.add_result(cpu_test.cpu_test())
   report.add_result(disks_test.disks_test())
   report.add_result(gpu_test.gpu_test())
   report.add_result(network_test.network_test())
   report.add_result(usb_test.usb_test())
   return report.save_report(path)


def main():
   args = parser.parse_args()

   if args.tui:
      tui.launch_tui()
      return

   if args.monitor:
      tui.launch_realtime_monitor()
      return

   if args.cpu:
      print("Running CPU Test...")
      _print_result(runner.cpu_test_runner())

   if args.disks:
      print("\nRunning Disks Test...")
      _print_result(runner.disks_test_runner())

   if args.gpu:
      print("\nRunning GPU Test...")
      _print_result(runner.gpu_test_runner())

   if args.network:
      print("\nRunning Network Test...")
      _print_result(runner.network_test_runner())

   if args.usb:
      print("\nRunning USB Test...")
      _print_result(runner.usb_test_runner())

   if args.all:
      print("Running all tests...")
      for result in _run_all_runners():
         _print_result(result)

   if args.report:
      print("\nRunning all tests for report...")
      report_path = _build_report(args.report)
      print(f"Report saved successfully to: {report_path}")

   if not any([args.cpu, args.disks, args.gpu, args.network, args.usb, args.all, args.report, args.tui, args.monitor]):
      parser.print_help()


if __name__ == "__main__":
   main()