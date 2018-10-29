import os
import subprocess

keypath = "/home/azureadmin/keys/"
cmd = "python /home/azureadmin/bin/ksignaudit.py"

class get_cmd():

    def __init__(self, path_to_result):
        self.path_to_results = path_to_result
        self.result_files = [x for x in os.listdir(self.path_to_results) if x.endswith('.pem')]

        mycmd = self.process_files()

        subprocess.call(mycmd, shell=True)

    def process_files(self):
        output_str = cmd
        for filename in self.result_files:
            output_str = output_str + " -s " + os.path.join(keypath, filename)
            
        return output_str
    
def main():
    app = get_cmd(keypath)
    
if __name__ == "__main__": main()
 
