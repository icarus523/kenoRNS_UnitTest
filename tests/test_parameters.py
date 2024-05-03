import unittest
import os
import subprocess

from datetime import datetime, date, timedelta
from rns2_result_audit import RNS2_UnitTest, TIMESTAMP_DRIFT_ONLY, RNSResult, \
    RNS2_Unzip, RNS2_LOGS_PATH, KEYPATH, RNS2_LOGS_PATH_OUTPUT, FILE_CONCATENATED_VERIFIED_SIGNED_LOGS

class test_parameters(RNS2_UnitTest):
    
    def test_parameter_check_keno(self): 
        # Test case to verify the parameters for each Keno game result
        self.time_stamp_dict_l = list() 
        self.starting_date = ''
        self.ending_date = ''

        json_file_l = [x for x in os.listdir(RNS2_LOGS_PATH_OUTPUT) if x.endswith('.json')]
        self.assertTrue(len(json_file_l) > 0)

        # Parameter check for each file
        for f in json_file_l:
            # calling: self.parametercheck_keno generates: 
            #  self.time_stamp_dict_l -- list of time stamp dicts
            self.assertTrue(self.parametercheck_keno(f))

        # sort
        device_entries = {}
        for entry in self.time_stamp_dict_l:
            device_id = entry.get('DeviceID', None)
            if device_id is not None:
                if device_id not in device_entries:
                    device_entries[device_id] = []
                device_entries[device_id].append(entry)

        # # Extract the device IDs and sort them alphabetically
        device_ids = sorted(device_entries.keys())
        self.assertTrue(len(device_ids) > 0)

        # # Create a list of entries for each device ID
        rnglist = [device_entries[device_id] for device_id in device_ids]
        self.assertTrue(len(rnglist) > 0)

        for device in rnglist:
            if len(device) != 0: 
                device_id = entry.get('DeviceID', None)
                # generate the average timestamp difference per day and write to file. 
                self.AverageDifferencePerDay(device, device_id)
                # write individual parameter check outputs to a file
                self.ParameterCheckOutput(device, device_id)

    # Test case to verify the zip archive file name are sequential based on date 
    # in the filename 
    @unittest.skipIf(TIMESTAMP_DRIFT_ONLY, "testing only time drift")
    def test_sequential_date(self):
        file_date_list = list()
        
        for filename in self.result_files:
            f = RNSResult(fname = filename)
            timestamp = datetime.strptime(f.time_stamp, '%Y-%m-%dT%M.%H.%S')
            file_date_list.append(timestamp)

        file_date_list_sorted = sorted(file_date_list) 

        self.assertTrue(len(file_date_list_sorted) > 0, len(file_date_list_sorted))
        
        generated_date_list = list()
        for x in range((file_date_list_sorted[-1] - file_date_list_sorted[0]).days): 
            generated_date_list.append(file_date_list_sorted[0] + timedelta(x))

        missing = set(sorted(generated_date_list)) - set(sorted(file_date_list_sorted))
    
        if len(missing) == 0: 
            print("\n\nNo Missing Keno Results")
        else: 
            print("\n\nMissing Keno Results: ")
            for date in missing:
                print("Date: " + date.strftime("%Y-%m-%d") + "; Filename: " + self.build_missing_filename(date))
                
        self.assertTrue(len(missing) == 0, len(missing))

    # Test case to verify the file size of each zip file. 
    @unittest.skipIf(TIMESTAMP_DRIFT_ONLY, "testing only time drift")
    def test_file_size(self):
        expected_fsize = 100000
        for filename in self.result_files:
            size_in_bytes = os.stat(os.path.join(self.path_to_results,filename))

            if size_in_bytes.st_size < expected_fsize:
                print("WARNING!: " + filename + ": is less than 100KB. Size is: " + str(size_in_bytes.st_size) + " bytes")
            
            err_msg = filename + " file size is less than expected size: " + str(size_in_bytes.st_size)
            self.assertTrue(size_in_bytes.st_size > expected_fsize, err_msg)


    # Test case to verify result file has been signed by an expected signing key
    @unittest.skipIf(TIMESTAMP_DRIFT_ONLY, "testing only time drift")
    def test_resultfile_with_signingkeys(self): 
        json_file_l = [x for x in os.listdir(RNS2_LOGS_PATH_OUTPUT) if x.endswith('.json')]
        
        signkey_list = [x for x in os.listdir(KEYPATH) if x.endswith('.pem')]
        # append "keys" to filename 
        signkey_list = [KEYPATH + "/" + s for s in signkey_list]
            
        for file in json_file_l:
            subprocess.call('java -jar bin/KenoSignAudit.jar ' + os.path.join(RNS2_LOGS_PATH_OUTPUT, file) +  
                ' ' + ' '.join(signkey_list) + ' > ' + file +'_signlog.out', shell=True)

        # cat all .out file in logevent file
        fileout_lists = [x for x in os.listdir('.') if x.endswith('.out')] # list_files(RNS2_RESULTS_PATH, ".out")
        self.concatenate_signlogfiles(fileout_lists)

        with open(FILE_CONCATENATED_VERIFIED_SIGNED_LOGS, 'r') as f: 
            for line in f: 
                # log to file for any fail or none
                if 'FAIL' in line or 'None' in line: 
                    self.log_fail_or_none(line)
                    
                self.assertFalse('Fail' in line)
                self.assertFalse('None' in line)    