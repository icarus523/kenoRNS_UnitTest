import os
import unittest
from datetime import datetime, date, timedelta

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
        self.path_to_results = 'G:\\OLGR-TECHSERV-TSS-FILES\\Keno\\Tabcorp\\KNG_new\\Results\\2017'
        self.result_files = [x for x in os.listdir(self.path_to_results) if x.endswith('.json.zip')]
        
    def test_sequential_date(self):
        file_date_list = list()
        
        for filename in self.result_files:
            f = RNSResult(fname = filename)
            timestamp = datetime.strptime(f.time_stamp, '%Y-%m-%dT%M.%H.%S')
            file_date_list.append(timestamp)

            # print(str(timestamp.strftime("%Y-%m-%d")))

        date_set = set(file_date_list[0] + timedelta(x) for x in range((file_date_list[-1] - file_date_list[0]).days))
        missing = sorted(date_set - set(file_date_list))

        print("\n\nMissing Keno Results: ")
        for date in missing:
            print(date.strftime("%Y-%m-%d"))

        self.assertTrue(len(missing) == 0)
        
    def test_file_size(self):
        for filename in self.result_files:
            size_in_bytes = os.stat(os.path.join(self.path_to_results,filename))

            if size_in_bytes.st_size < 100000:
                print("WARNING!: " + filename + ": is less than 100KB. Size is: " + str(size_in_bytes.st_size) + " bytes")

            self.assertTrue(size_in_bytes.st_size > 100000)

if __name__ == '__main__':
    unittest.main()
