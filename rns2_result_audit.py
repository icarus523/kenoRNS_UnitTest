import os
import unittest
import json
import subprocess
import zipfile
import logging
import dateutil.parser
import time

import xml.etree.ElementTree as etree
from xml.etree.ElementTree import ElementTree

from datetime import datetime, date, timedelta
from statistics import mean

# path to zipped rns2files
RNS2_LOGS_PATH = "rns2_results_unzipped"
RNS2_LOGS_PATH_OUTPUT = "rns2results"
KEYPATH = "keys"

# file names
FILE_FAIL_OR_NONE='fail_or_none_output.txt'
FILE_LOG = 'signparalog.out'
FILE_CONCATENATED_VERIFIED_SIGNED_LOGS = 'signlog.txt'

# Set to True if you only want to generate results for timestamp drift
TIMESTAMP_DRIFT_ONLY = False

class RNS2ResultEmail: 

    def __init__(self, start_date, end_date, result_d): 
        self.start_date = start_date
        self.end_date = end_date
        self.result_d = result_d

        self.draft_email()

    def draft_email(self):
        header = "An audit of the Keno QLDRNS results log file for the following period have been completed:\n\n"
        result = "Results:\n\nAll Keno QLD RNS results files passed signature and integrity checks. See below for details.\n"
        path_to_result = result_d['path_to_result']

        pass

class RNS2_Unzip: 
    # class to unzip RNS zipped log files 
    
    def __init__(self, path_to_result):
        self.path_to_results = path_to_result
        
        self.result_files = [x for x in os.listdir(self.path_to_results) if x.endswith('.json.zip')]
        assert(len(self.result_files) > 0)
        
        self.process_files()

    def process_files(self):
        for filename in self.result_files:
            self.unzip(os.path.join(RNS2_LOGS_PATH, filename), RNS2_LOGS_PATH_OUTPUT)

        self.result_json_files = [x for x in os.listdir(RNS2_LOGS_PATH_OUTPUT) if x.endswith('.json')]
        for json_filename in self.result_json_files:
            size_in_bytes = os.stat(os.path.join(RNS2_LOGS_PATH_OUTPUT, json_filename))

            if size_in_bytes.st_size < 2000:
                os.remove(os.path.join(RNS2_LOGS_PATH_OUTPUT, json_filename)) # delete!

    def unzip(self, source_filename, dest_dir):
        with zipfile.ZipFile(source_filename) as zf:          
            uncompress_size = sum((file.file_size for file in zf.infolist())) 
            extracted_size = 0
            #print('uncompressed size: ' + str(uncompress_size) + ' bytes')

            # print("Unzipping...")
            for file in zf.infolist():
                extracted_size += file.file_size
                percentage = extracted_size * 100/uncompress_size
                # self.pBar["value"] = percentage
                # print(file.filename + ": %6.2f %%\r" % (float(percentage)))
                zf.extract(file, dest_dir)

class RNSResult:
    # helper class for RNS2 Results

    def __init__(self, fname):
        fields = str(fname).split('_')
        self.header = fields[0]
        self.host = fields[1]
        tmp = fields[2]

        # strip suffix '.json.zip' from time stamp:
        self.time_stamp = tmp[:-15]

        assert(len(fields) == 3)
        
class RNS2_UnitTest(unittest.TestCase):

    def setUp(self):
        self.path_to_results = RNS2_LOGS_PATH
        self.json_results = RNS2_LOGS_PATH_OUTPUT
        self.result_files = [x for x in os.listdir(self.path_to_results) if x.endswith('.json.zip')]
        
    def tearDown(self):
        json_file_l = [x for x in os.listdir(self.json_results) if x.endswith('.json')]

        # delete unzipped files            
        for f in json_file_l:
            if os.path.isfile(f): 
                os.remove(f)

    def concatenate_signlogfiles(self, filenames):
        with open(FILE_CONCATENATED_VERIFIED_SIGNED_LOGS, 'w') as outfile:
            for fname in filenames:
                outfile.write("Check signature for file : " + fname + "\n")
                with open(fname) as file:
                    for line in file:
                        if not line.isspace():
                            outfile.write(line)
                os.remove(fname)

    def build_missing_filename(self, date):
        ts = date.strftime("%Y-%m-%dT%M.%H.%S")
        return "results_QLDRNS-production_" + ts + ".json.zip"

    def logstringtofile(self, stringnames):
        with open(FILE_LOG, 'a+') as outfile:
            outfile.write(stringnames)

    def log_fail_or_none(self, line): 
        with open(FILE_FAIL_OR_NONE,'a+') as f: 
            f.writelines(line)

    def getAverage(self, itemlist):
        if len(itemlist) == 0:
            return 0
            
        sum_num = 0
        for item in itemlist: 
            # RFC 3339 format
            timestamp = dateutil.parser.isoparse(item['timestamp']) 
            signerTimestamp = dateutil.parser.isoparse(item['signerTimestamp'])
            difference =  signerTimestamp - timestamp
        
            sum_num = sum_num + abs(difference.total_seconds())

        avg = sum_num / len(itemlist)
        
        return avg
    
    def getDevice(self, itemlist): 
        if len(itemlist) == 0:
            return "unknown"
            
        return itemlist[0]['DeviceID']
    # verifies parameters in the JSON result file for Keno games
    # input: json result file path
    # output: boolean: True | False
    #   will write to log file should tests fail
    # <timestamp>2021-06-15T14:01:21.972Z</timestamp><signerTimestamp>2021-06-16T00:14:10.000Z</signerTimestamp>
    def parametercheck_keno(self, resultsJsonFile):
        MAXIMUM_TIMESTAMP_DIFFERENCE = 300
        with open(os.path.join(RNS2_LOGS_PATH_OUTPUT, resultsJsonFile), 'r') as f:
            json_data = json.load(f)

            for result in json_data['results']:
                KenoID = result['result']['resultId']
                DeviceID = result['result']['deviceId']
                resultXml = etree.fromstring(result['result']['result'].encode('utf-8'))
                for child in resultXml:
                    # print(child.tag, child.attrib)
                    jsrel = child.findtext('{urn:envelope}results')
                    jpara = child.find('{urn:envelope}parameters')
                    jnumset = jpara.findtext('{urn:envelope}numberOfSets')
                    #print(jnumset)
                    if (int(jnumset) != 1):
                        self.logstringtofile("Keno ID : " + KenoID + " Result check numberOfSets:  FAIL ")
                        return False
                    jcount = jpara.findtext('{urn:envelope}count')
                    #print(jcount)
                    if (int(jcount) != 20):
                        self.logstringtofile("Keno ID : " + KenoID + " Result check count: FAIL ")
                        return False

                    jrange = jpara.findall('{urn:envelope}range')
                    #print("range ; ", " ".join(jrange))

                    # check range parameters
                    for item in jrange:
                        for k,v in item.attrib.items():
                            #print(k, v)
                            if (k=="max" and (int(v) !=80)):
                                self.logstringtofile("Keno ID : " + KenoID + " Result check range max: FAIL ")
                                return False
                            if (k=="min" and (int(v) !=1)):
                                self.logstringtofile("Keno ID : " + KenoID + " Result check range min: FAIL ")
                                return False

                    jreplacement = jpara.findtext('{urn:envelope}replacement')
                    #print(jreplacement)
                    if (jreplacement != "false"):
                        self.logstringtofile("Keno ID : " + KenoID + " Result check replacement: FAIL ")
                        return False

                    jweighting= jpara.findtext('{urn:envelope}weighting')
                    #print("weigth: ", jweighting)
                    if (jweighting is not None):
                        self.logstringtofile("Keno ID : " + KenoID + " Result check weighting: FAIL ")
                        return False
                    jsver = child.find('{urn:envelope}verificationContext')
                    jtimestamp = child.findtext('{urn:envelope}timestamp')
                    jsignerTimestamp = child.findtext('{urn:envelope}signerTimestamp')

                    #timestamp = datetime.strptime(jtimestamp, '%Y-%m-%dT%H:%M:%S%z')
                    #jsignerTimestamp = datetime.strptime(jsignerTimestamp, '%Y-%m-%dT%H:%M:%S.%z')
                    timestamp = dateutil.parser.isoparse(jtimestamp) # RFC 3339 format
                    signerTimestamp = dateutil.parser.isoparse(jsignerTimestamp)

                    difference =  signerTimestamp - timestamp
                    
                    self.time_stamp_difference.append(difference)                    
                    
                    # display all differences
                    s = "resultId: " + KenoID + " DeviceID: " + DeviceID + " signerTimestamp: " + str(signerTimestamp) \
                            + " timestamp: " + str(timestamp) + " Difference (secs): " + str(abs(difference.total_seconds()))
                    self.output_str.append(s)
                                        
                    
                    # only generate average for results that exceed the max timestamp difference
                    #if abs(difference.total_seconds()) > MAXIMUM_TIMESTAMP_DIFFERENCE:
                    #    self.logstringtofile("resultId: " + KenoID + " DeviceID: " + DeviceID + " signerTimestamp: " + str(signerTimestamp) 
                    #        + " timestamp: " + str(timestamp) + " Difference (secs): " + str(abs(difference.total_seconds())))
                                                
                    entry = dict()                        
                    entry['signerTimestamp'] = str(signerTimestamp)
                    entry['timestamp'] = str(timestamp)
                    entry['KenoID'] = KenoID                                           
                    entry['DeviceID'] = DeviceID
                                           
                    self.time_stamp_dict_l.append(entry)
                                                   
                        # return False

                    if self.starting_date == '':
                        self.starting_date = timestamp
                    else: 
                        if timestamp < self.starting_date: 
                            self.starting_date = timestamp
                            
                    if self.ending_date == '':
                        self.ending_date = timestamp
                    else: 
                        if timestamp > self.ending_date:
                            self.ending_date = timestamp

                    jsgnum = jsver.findtext('{urn:envelope}gameNumber')
                    jsgnrel = str(int(jsgnum)) + "," + jsrel
                    if(jsrel !=0):
                        break

        return True
    # #################### U N I T T E S T S #########################
    # Test case to verify the parameters for each Keno game result
    def test_parameter_check_keno(self): 
        self.unzipped_files = RNS2_Unzip(RNS2_LOGS_PATH)
        self.json_file_l = [x for x in os.listdir(self.json_results) if x.endswith('.json')]
        self.time_stamp_difference = list() 
        self.time_stamp_dict_l = list() 
        self.output_str = list() 
        self.starting_date = ''
        self.ending_date = ''
        
        # Parameter check for each file
        for f in self.json_file_l:
            self.assertTrue(self.parametercheck_keno(f))

        qldtbknrng01_entries = list()
        qldtbknrng02_entries = list() 
        qldtbknrng03_entries = list()
        qldtbknrng04_entries = list() 
        
        # sort
        for entry in self.time_stamp_dict_l:
            for k,v in entry.items(): 
                if k == 'DeviceID': 
                    if v == 'qldtbknrng01': 
                        qldtbknrng01_entries.append(entry)
                    elif v == 'qldtbknrng02': 
                        qldtbknrng02_entries.append(entry)
                    elif v == 'qldtbknrng03': 
                        qldtbknrng03_entries.append(entry)
                    elif v == 'qldtbknrng04':
                        qldtbknrng04_entries.append(entry)

        rnglist = [qldtbknrng01_entries, qldtbknrng02_entries, qldtbknrng03_entries, qldtbknrng04_entries]

        for device in rnglist:
            avg = 0
            if len(device) != 0: 
                deviceID = device[0]['DeviceID']
                avg = self.getAverage(device)
                
                avg_HMS_str = time.strftime("%H:%M:%S", time.gmtime(avg))
                fname = deviceID + " - " + self.starting_date.strftime("%d-%m-%Y") + " to " + self.ending_date.strftime("%d-%m-%Y") +  " - unittest_results.txt"
                with open(fname, 'w+') as f:
                    for entry in self.output_str:
                        if deviceID in entry:
                            f.write("\n" + entry) # write output str to file

                    f.write("\n\n" + deviceID + " - The average time stamp difference (signingTimeStamp - timeStamp) is: " + avg_HMS_str + " or " + str(round(avg,2)) + " (secs)")

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
        self.unzipped_files = RNS2_Unzip(RNS2_LOGS_PATH)
        json_file_l = [x for x in os.listdir(self.json_results) if x.endswith('.json')]
        
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
                    
if __name__ == '__main__':
    unittest.main()
