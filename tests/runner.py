"Test runner."

import unittest

import test_api_root
import test_api_about
import test_api_user
import test_api_links
import test_api_dataset
import test_api_graphic

loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.loadTestsFromModule(test_api_root))
suite.addTests(loader.loadTestsFromModule(test_api_about))
suite.addTests(loader.loadTestsFromModule(test_api_user))
suite.addTests(loader.loadTestsFromModule(test_api_links))
suite.addTests(loader.loadTestsFromModule(test_api_dataset))
suite.addTests(loader.loadTestsFromModule(test_api_graphic))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
