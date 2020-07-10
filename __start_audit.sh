#!/bin/sh

# cleanup
rm rns2_results_unzipped/*
rm *.txt
# rm keys/*
# rm rns2results/*

# perform unittest
python3 -m unittest rns2_result_audit.py --verbose # > unittest_result.txt