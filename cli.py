import runner
import pprint
import time
import tests.cpu_test as cpu
import tests.disks_test as disks

def main():
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

   print("\nRunning Disks Test...")
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