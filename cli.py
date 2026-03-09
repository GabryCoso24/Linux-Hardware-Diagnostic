import runner
import pprint
import time
import argparse as ap
import core.report as report_gen
import tests.cpu_test as cpu_test
import tests.disks_test as disks_test
from datetime import datetime
import os

parser = ap.ArgumentParser(description="Hardware Diagnostic Tool")
parser.add_argument("--cpu", action="store_true", help="Run CPU test")
parser.add_argument("--disks", action="store_true", help="Run Disks test")
parser.add_argument("--all", action="store_true", help="Run all tests")
parser.add_argument("--report", nargs='?', const='auto', help="Save report to file (optional: specify filename or leave empty for auto-generated name)")

def main():
   args = parser.parse_args()
    
   if args.cpu:
      print("Running CPU Test...")
      cpu_result = runner.cpu_test_runner()
      time.sleep(1)
      print("CPU Test Result:", cpu_result["status"])
      time.sleep(1)
      print("CPU Test Message:", cpu_result["message"])
      time.sleep(1)
      print("CPU Test Data:")
      pprint.pprint(cpu_result["data"])
      time.sleep(1)
   elif args.disks:
      print("\nRunning Disks Test...")
      time.sleep(1)
      disks_result = runner.disks_test_runner()
      print("Disks Test Result:", disks_result["status"])
      time.sleep(1)
      print("Disks Test Message:", disks_result["message"])
      time.sleep(1)
      print("Disks Test Data:")
      pprint.pprint(disks_result["data"])
   elif args.report:
      print("\nRunning all tests for report...")
      time.sleep(1)
      
      # Run CPU test
      print("Running CPU Test...")
      cpu_result = cpu_test.cpu_test()
      print("CPU Test Result:", cpu_result.status.value)
      time.sleep(1)
      
      # Run Disks test
      print("Running Disks Test...")
      disks_result = disks_test.disks_test()
      print("Disks Test Result:", disks_result.status.value)
      time.sleep(1)
      
      # Create report with results
      report = report_gen.Report()
      report.add_result(cpu_result)
      report.add_result(disks_result)
      
      print(f"\nSaving report...")
      report_path = report.save_report(args.report)
      print(f"Report saved successfully to: {report_path}")
   elif args.all:
      print("Running all tests...")
      time.sleep(1)
      cpu_result = runner.cpu_test_runner()
      print("CPU Test Result:", cpu_result["status"])
      time.sleep(1)
      print("CPU Test Message:", cpu_result["message"])
      time.sleep(1)
      print("CPU Test Data:")
      pprint.pprint(cpu_result["data"])
      time.sleep(1)
      disks_result = runner.disks_test_runner()
      print("Disks Test Result:", disks_result["status"])
      time.sleep(1)
      print("Disks Test Message:", disks_result["message"])
      time.sleep(1)
      print("Disks Test Data:")
      pprint.pprint(disks_result["data"])


if __name__ == "__main__":
   main()