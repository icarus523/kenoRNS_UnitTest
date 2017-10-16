# kenoRNS_UnitTest
Unit Testing for Keno RNS results. 

The following tests have been implemented: 
1. Sequential Date (from the earliest date in the directory to the latest file)
2. File Size > 100kb

## How to use: 

1. Edit the file and change the following line as appropriate: 
`self.path_to_results = 'G:\\OLGR-TECHSERV-TSS-FILES\\Keno\\Tabcorp\\KNG_new\\Results\\2017'`

2. Press F5 to run or in the command line type: `py -m unittest -v rns2_results_unit_test.py`
