import os
import zipfile

RNS2_LOGS_PATH = "C:\\Users\\aceretjr\\Documents\\dev\\RNS2MissingResults\\rns2\\"
RNS2_LOGS_PATH_OUTPUT = "C:\\Users\\aceretjr\\Documents\\dev\\RNS2MissingResults\\rns2\\output"

### IMPORTANT
### Make sure you are not using the RNS2 result files from G:\OLGR-TECHSERV-TSS-FILES\Keno\Tabcorp\KNG_new\Results
### Always work on a local copy, as this script deletes files!

class RNS2_Unzip(): 

    def __init__(self, path_to_result):
        self.path_to_results = path_to_result
        self.result_files = [x for x in os.listdir(self.path_to_results) if x.endswith('.json.zip')]

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

            print("Unzipping...")
            for file in zf.infolist():
                extracted_size += file.file_size
                percentage = extracted_size * 100/uncompress_size
                #self.pBar["value"] = percentage
                print(file.filename + ": %6.2f %%\r" % (float(percentage)))
                zf.extract(file, dest_dir)

def main():
    app = RNS2_Unzip(RNS2_LOGS_PATH)

if __name__ == "__main__": main()
