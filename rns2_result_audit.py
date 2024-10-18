import os
import unittest
import json
import subprocess
import zipfile
import logging
import dateutil.parser
import time
import re

import xml.etree.ElementTree as etree
from xml.etree.ElementTree import ElementTree

from datetime import datetime, date, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend

# path to zipped rns2files
RNS2_LOGS_PATH = "rns2_results_unzipped"
RNS2_LOGS_PATH_OUTPUT = "rns2results"
KEYPATH = "keys"

# file names
FILE_FAIL_OR_NONE='fail_or_none_output.txt'
FILE_LOG = 'signparalog.out'
FILE_CONCATENATED_VERIFIED_SIGNED_LOGS = 'signlog.txt'

# Set to True if you only want to generate results for timestamp drift
# by default, keep this to false
TIMESTAMP_DRIFT_ONLY = False

EXPECTED_DEVICE_IDS = ['prddc2krng301', 'prddc2krng302', 'prddc1krng301', 'prddc1krng302', 'qldtbknrng04']
PATH_TO_CERTS = "keys/"
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
        if not path_to_result: 
            self.path_to_results = RNS2_LOGS_PATH
        else:
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
        self.path_to_results = RNS2_LOGS_PATH # unzipped archives
        self.result_files = [x for x in os.listdir(RNS2_LOGS_PATH) if x.endswith('.json.zip')]
        RNS2_Unzip(self.path_to_results)
        
    def tearDown(self):
        json_file_l = [x for x in os.listdir(RNS2_LOGS_PATH_OUTPUT) if x.endswith('.json')]

        # delete json files            
        for f in json_file_l:
            if os.path.isfile(f): 
                os.remove(f)

        # delete zip files
        # do here

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

    def logstringtofile(self, line):
        with open(FILE_LOG, 'a+') as f:
            f.writelines(line)

    def log_fail_or_none(self, line): 
        with open(FILE_FAIL_OR_NONE,'a+') as f: 
            f.writelines(line)

    def getDevice(self, itemlist): 
        if len(itemlist) == 0:
            return "unknown"
            
        return itemlist[0]['DeviceID']

    def is_valid_date(self, date_str): 
        try:
            datetime.strptime(date_str, "%d%m%y")
            return True
        except ValueError: 
            return False

    def is_valid_timestamp(self, timestamp_str):
        try:
            # Define the expected format
            datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            return True
        except ValueError:
            return False

    def contains_xml_metacharacters(self, string):
        # Define a regular expression pattern for XML metacharacters
        pattern = r"[&<>\"']"
        # Search for the pattern in the string
        return bool(re.search(pattern, string))

    def is_sha256_hash(self, string):
        # Define a regular expression pattern for a 64-character hexadecimal string
        pattern = r"^[a-fA-F0-9]{64}$"
        # Check if the string matches the pattern
        return bool(re.match(pattern, string))

    def verifyKenoParameterDrawRequest(self, p):
        return (
            p["numberOfSets"] == 1 and
            p["range"]["min"] == 1 and
            p["range"]["max"] == 80 and
            p["count"] == 20 and
            p["replacement"] == False and
            p["weighting"] == None
        )

    def verify_verificationContext_DrawRequest(self, p): 
        return (
                self.is_valid_date(p["gameDate"]) and 
                p["gameNumber"].isdigit() and
                not self.contains_xml_metacharacters(p["gameNumber"]) and
                self.is_sha256_hash(p["digest"]) and
                not self.contains_xml_metacharacters(p["digest"])
        )


    def load_pem_cert(self, pem_data):
        return x509.load_pem_x509_certificate(pem_data.encode(), default_backend())

    def verify_device_cert(self, directory_path, cert_string):
        cert_to_match = self.load_pem_cert(cert_string)

        for filename in os.listdir(directory_path):
            if filename.endswith(".pem"):
                pem_file_path = os.path.join(directory_path, filename)
                assert(os.path.isfile(pem_file_path))
                with open(pem_file_path, 'r') as pem_file:
                    pem_data = pem_file.read()
                    pem_cert = self.load_pem_cert(pem_data) 
                    print(pem_cert, cert_to_match)

                    if pem_cert == cert_to_match: 
                        return True
        
        return False

    # verifies parameters in the JSON request data structure in the result file for Keno games
    # input: json result file
    # output: boolean: True | False
    #   will write to log file should tests fail. 
    #  Sample request field: 
    # "request" : "{\"resultId\":\"keno-qld-240601-463\",\"type\":\"keno-qld\",\"parameters\":{\"numberOfSets\":1,\"range\":{\"min\":1,\"max\":80},\"count\":20,\"replacement\":false,\"weighting\":null},\"verificationContext\":{\"gameDate\":\"240601\",\"digest\":\"308dcd523a3ba04fe1f7939368efc1177b47890d0f535e61ea9d136dd5ae7e8a\",\"gameNumber\":\"463\"},\"info\":null}",
    def request_parametercheck_keno(self, resultsJsonFile): 
        with open(os.path.join(RNS2_LOGS_PATH_OUTPUT, resultsJsonFile), 'r') as f:
            json_data = json.load(f)

            for results in json_data['results']:
                resultId = results['result']['resultId']
                DeviceID = results['result']['deviceId']
                request_json = json.loads(results['result']['request'].encode('utf-8'))

                if request_json['resultId'] != resultId: 
                    self.logstringtofile("Keno ID : " + resultId + " request resultId check - expected: + " + resultId + ":  FAIL ")
                    return False

                if request_json['type'] != 'keno-qld': 
                    self.logstringtofile("Keno ID : " + resultId + " request type check - not 'keno-qld':  FAIL ")
                    return False

                if not self.verifyKenoParameterDrawRequest(request_json['parameters']):
                    self.logstringtofile("Keno ID : " + resultId + " request draw parameters check:  FAIL ")
                    return False

                if not self.verify_verificationContext_DrawRequest(request_json["verificationContext"]):
                    self.logstringtofile("Keno ID : " + resultId + " request verificationContext parameters check:  FAIL ")
                    return False                    

        return True

    # verifies parameters in the JSON result file for Keno games
    # input: json result file path
    # output: boolean: True | False
    #   will write to log file should tests fail
    # <timestamp>2021-06-15T14:01:21.972Z</timestamp><signerTimestamp>2021-06-16T00:14:10.000Z</signerTimestamp>
    # ,"verificationContext\":{\"gameDate\":\"240601\",\"digest\":\"a0ee85c9718e8ba02bf629af912b7893b28ee1ce8e2e060bb0b9b266ad5a287e\",\"gameNumber\":\"464\"},
    # verifies all fields (other than request)
    def result_parametercheck_keno(self, resultsJsonFile):
        with open(os.path.join(RNS2_LOGS_PATH_OUTPUT, resultsJsonFile), 'r') as f:
            json_data = json.load(f)

            for result in json_data['results']:
                KenoID = result['result']['resultId']
                DeviceID = result['result']['deviceId']
                ResultSerial = result['result']['resultSerial']
                InternalID = result['result']['internalId']
                Info = result['result']['info']
                Timestamp = result['result']['timestamp']
                DeviceAuthCert = result['result']['deviceCert'] # For Keno RNS the DeviceCert is the authkey not signing key

                # if not self.verify_device_cert(PATH_TO_CERTS, DeviceCert):
                #     self.logstringtofile("Keno ID : " + KenoID + " deviceCert is unknown :  FAIL ")
                #     return False                     

                if not self.is_valid_timestamp(Timestamp): 
                    self.logstringtofile("Keno ID : " + KenoID + " timestamp is not valid - " + Timestamp + ":  FAIL ")
                    return False                        

                if InternalID != ResultSerial:
                    self.logstringtofile("Keno ID : " + KenoID + " internalId does not match resultSerial - InternalID=" + InternalID + " - ResultID=" + DeviceID + ":  FAIL ")
                    return False                        

                if Info: 
                    self.logstringtofile("Keno ID : " + KenoID + " info field is not nil - info:" + Info + ":  FAIL ")
                    return False                                   

                if not DeviceID in EXPECTED_DEVICE_IDS:
                    self.logstringtofile("Keno ID : " + KenoID + " DeviceID unknown - " + DeviceID + ":  FAIL ")
                    return False                    

                # verify 'result' field (XML) data
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

                    # test for XML injection attack in the verificationContext field for RNS draws
                    gameNumber = jsver.findtext('{urn:envelope}gameNumber')
                    # print("gameNumber is: " + str(gameNumber))
                    # self.assertTrue(gameNumber.isdigit())
                    if not gameNumber.isdigit(): 
                        self.logstringtofile("Keno ID : " + KenoID +  " verificationContext - gameNumber not a digit: FAIL ")
                        return False

                    if self.contains_xml_metacharacters(gameNumber): 
                        self.logstringtofile("Keno ID : " + KenoID +  " verificationContext - gameNumber contains XML metacharacters: FAIL ")
                        return False

                    digest = jsver.findtext('{urn:envelope}digest')
                    # print("digest is: " + str(digest))
                    # self.assertTrue(self.is_sha256_hash(digest))
                    if not self.is_sha256_hash(digest): 
                        self.logstringtofile("Keno ID : " + KenoID +  " verificationContext - digest not a SHA256 hash: FAIL ")
                        return False                        

                    if self.contains_xml_metacharacters(digest): 
                        self.logstringtofile("Keno ID : " + KenoID +  " verificationContext - digest contains XML metachars: FAIL ")
                        return False

                    gameDate = jsver.findtext('{urn:envelope}gameDate')
                    # print("gameDate is: " + str(gameDate))
                    # self.assertTrue(self.is_valid_date(gameDate))
                    if not self.is_valid_date(gameDate): 
                        self.logstringtofile("Keno ID : " + KenoID +  " verificationContext - gameDate not a valid date: FAIL ")
                        return False                        

                    if self.contains_xml_metacharacters(gameDate): 
                        self.logstringtofile("Keno ID : " + KenoID +  " verificationContext - gameDate contains XML metachars: FAIL ")
                        return False

                    jtimestamp = child.findtext('{urn:envelope}timestamp')
                    jsignerTimestamp = child.findtext('{urn:envelope}signerTimestamp')

                    timestamp = dateutil.parser.isoparse(jtimestamp) # RFC 3339 format
                    signerTimestamp = dateutil.parser.isoparse(jsignerTimestamp)
                    difference =  signerTimestamp - timestamp

                    # save entry into a list of dicts
                    self.time_stamp_dict_l.append({
                        'signerTimestamp': signerTimestamp,
                        'timestamp': timestamp,
                        'KenoID': KenoID,
                        'DeviceID': DeviceID,
                        'difference': abs(difference.total_seconds())
                    })

                    # update starting_date
                    if self.starting_date == '':
                        self.starting_date = timestamp
                    else: 
                        if timestamp < self.starting_date: 
                            self.starting_date = timestamp
                    
                    # update ending_date
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

    def AverageDifferencePerDay(self, device, deviceID): 
    def AverageDifferencePerDay(self, device_l, deviceID): 
        # get timestamps to calculate differences
        differences_per_day = {}
        for entry in device_l:
            timestamp = entry["timestamp"]
            signer_timestamp = entry["signerTimestamp"]
            date = timestamp.date()
            if date not in differences_per_day:
                differences_per_day[date] = []
            difference = (signer_timestamp - timestamp).total_seconds()
            differences_per_day[date].append(difference)                    

        # Calculate average difference per day
        average_diff_per_day = {}
        for date, differences in differences_per_day.items():
            average_diff_per_day[date] = sum(differences) / len(differences)

        # Calculate overall average difference
        overall_average_diff = sum(sum(differences) for differences in differences_per_day.values()) / sum(len(differences) for differences in differences_per_day.values())
        fname = deviceID + " - " + self.starting_date.strftime("%d-%m-%Y") + " to " + self.ending_date.strftime("%d-%m-%Y") +  " - avg timestamp diff per day.txt"        
        with open(fname, 'w+') as f:
            f.write("\n" + "deviceID: " + deviceID )
            for date, average_diff in average_diff_per_day.items():
                f.write("\n" + str(date) + "\t" + str(round(average_diff, 2)))

    def ParameterCheckOutput(self, device, deviceID):
    def ParameterCheckOutput(self, device_l, deviceID):
        # write output str to file        
        fname = f"{deviceID} - {self.starting_date.strftime('%d-%m-%Y')} to {self.ending_date.strftime('%d-%m-%Y')} - unittest_results.txt"

        with open(fname, 'w+') as f:
            for entry in device_l:
                if entry['DeviceID'] == deviceID:
                    s = (f"resultId: {entry['KenoID']} DeviceID: {entry['DeviceID']} "
                         f"signerTimestamp: {entry['signerTimestamp']} "
                         f"timestamp: {entry['timestamp']} Difference (secs): {entry['difference']}")
                    f.write("\n" + s)
                    
if __name__ == '__main__':
    unittest.main()
