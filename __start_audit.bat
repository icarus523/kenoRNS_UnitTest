@echo off

REM This script is to be run in a Windows environment.
REM Ensure that Java Runtime Environment (JRE) is installed.

REM Cleanup
REM Remove zipped archives
REM rmdir /s /q rns2_results_unzipped  (Uncomment if needed)

REM Remove previous outputs
del /q *.txt

REM Remove keys used
REM rmdir /s /q keys  (Uncomment if needed)

REM Remove .out files
del /q *.out

REM Remove results extracted
REM rmdir /q rns2results\*.json

REM Perform unit tests
python -m unittest discover -s tests -v

REM signlog.txt
REM Note: This is the final log of the Java application used to test certs/signatures
