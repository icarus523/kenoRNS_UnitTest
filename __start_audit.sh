#!/bin/sh

# This script is to be run in a sh environment. i.e. Linux. 
# The environment, needs to have JRE installed. 

# cleanup
# remove zipped archives 
# rm rns2_results_unzipped/*

# remove previous outputs
rm *.txt

# remove keys used
# rm keys/*

# remove .out files
rm *.out

# remove results extracted
rm rns2results/*

# perform unit tests
python3 -m unittest rns2_result_audit.py -v

# signlog.txt
# Note: This is the final log of the java application used to test certs/signatures