# kenoRNS_UnitTest
Unit Testing for Keno RNS results. 

The following tests have been implemented: 
1. Sequential Date (from the earliest date in the directory to the latest file)
2. File Size > 100kb
3. Validates all Keno RNS request parameters against expected parameters
4. Calculates the average clock time drift, across all draws performed. 

## How to use: 

Requires: 
Linux environment, with python3 installed. 
All dependencies should be in the venv-KenoRNSAudit

0. Enter the python3 virtual environment in Linux. i.e.
> source venv-KenoRNSAudit/bin/activate

1. Copy the zip Keno Results to the directory: rns2_results_unzipped
> cp G:\OLGR-TECHSERV-TSS-FILES\Keno\Tabcorp\KNG_new\Results\2022\*.zip C:\Users\Public\Documents\Keno_RNS2_Result_Audit_venv\rns2_results_unzipped\

Note: 
Always make copies of files, and don't link directly to the network drives! 
This script deletes files when complete. 

2. run the shell script: 
> sh __start_audit.sh

3. Save the results: 

> signlog.txt
> qldtbknrng04 - 31-12-2021 to 15-01-2022 - unittest_results.txt

4. Review results. 
> cat signlog.txt
	- ensure that all resultIds have an entry for "signed-by", e.g: 
	
resultId: keno-qld-211231-498  self-verified: OK  signed-by: keys/signingkey-11-12-2020-RNS4.pem
resultId: keno-qld-211231-499  self-verified: OK  signed-by: keys/signingkey-11-12-2020-RNS4.pem
resultId: keno-qld-211231-500  self-verified: OK  signed-by: keys/signingkey-11-12-2020-RNS4.pem
resultId: keno-qld-211231-501  self-verified: OK  signed-by: keys/signingkey-11-12-2020-RNS4.pem
resultId: keno-qld-211231-502  self-verified: OK  signed-by: keys/signingkey-11-12-2020-RNS4.pem
resultId: keno-qld-211231-503  self-verified: OK  signed-by: keys/signingkey-11-12-2020-RNS4.pem

Ensure the end of unittest displays: 

(venv-KenoRNSAudit) james@J2091408:/mnt/c/Users/Public/Documents/Keno_RNS2_Result_Audit_venv$ sh __start_audit.sh
rm: cannot remove '*.txt': No such file or directory
test_file_size (rns2_result_audit.RNS2_UnitTest) ... ok
test_parameter_check_keno (rns2_result_audit.RNS2_UnitTest) ... ok
test_resultfile_with_signingkeys (rns2_result_audit.RNS2_UnitTest) ... ok
test_sequential_date (rns2_result_audit.RNS2_UnitTest) ...

No Missing Keno Results
ok

----------------------------------------------------------------------
Ran 4 tests in 64.129s

OK


