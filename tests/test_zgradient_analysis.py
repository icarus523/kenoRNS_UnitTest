import unittest
import os
import subprocess

from rns2_result_audit import RNS2_UnitTest, TIMESTAMP_DRIFT_ONLY, RNSResult, \
    RNS2_Unzip, RNS2_LOGS_PATH, KEYPATH, RNS2_LOGS_PATH_OUTPUT, FILE_CONCATENATED_VERIFIED_SIGNED_LOGS

class test_zgradient_analysis(RNS2_UnitTest):
    output_dir = "."
    
    def find_files(self, directory, pattern):
        matched_files = []
        for filename in os.listdir(directory):
            if pattern in filename and filename.endswith(".txt"):
                matched_files.append(os.path.join(directory, filename))
        return matched_files

    def test_plot_graph(self):
        avg_diff_files = self.find_files(".", "avg timestamp diff per day.txt")
        if not avg_diff_files:
            print("[ERROR] No *-avg timestamp diff per day.txt files found. Aborting.")
            return

        unittest_results_files = self.find_files(".", "unittest_results")
        if not unittest_results_files:
            print("[ERROR] No *-unittest_results.txt files found. Aborting.")
            return

        for avg_diff_file in avg_diff_files:
            # Extract device ID from filename for logging
            device_id = avg_diff_file.split(" - ")[0]
            print(f"[INFO] Processing device: {device_id}")
            print(f"[INFO] average_diff_file is: {avg_diff_file}")

            # Find corresponding unittest_results file for this device
            matching_unittest_files = [f for f in unittest_results_files if device_id in f]
            if not matching_unittest_files:
                print(f"[ERROR] No unittest_results.txt found for device {device_id}")
                continue

            unittest_results_file = matching_unittest_files[0]
            print("[INFO] unittest_results_file is: " + unittest_results_file)

            self.generate_gradient_analysis(
                avg_diff_filename=avg_diff_file,
                unittest_results_filename=unittest_results_file
            )
