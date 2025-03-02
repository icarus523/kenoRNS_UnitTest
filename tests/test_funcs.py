import unittest
import os

from rns2_result_audit import RNS2_UnitTest

# these files must not be deleted as they have been confirmed to be good/bad formats. 
GOOD_TEST_FILE_PARAMETER_CHECKS=os.path.join('test_files', 'results_2024-06-02T00.00.00+10.00_QLDRNS-3_10.163.24.20.json')
BAD_TEST_FILE_PARAMETER_CHECKS=os.path.join('test_files', 'bad_results_2024-06-03T00.00.00+10.00_QLDRNS-3_10.163.24.20.json')

class test_funcs(RNS2_UnitTest):

	def test_request_parametercheck_keno_good_testfile(self): 

		self.assertTrue(self.request_parametercheck_keno(GOOD_TEST_FILE_PARAMETER_CHECKS))

	def test_request_parametercheck_keno_bad_testfile(self): 

		self.assertFalse(self.request_parametercheck_keno(BAD_TEST_FILE_PARAMETER_CHECKS))
