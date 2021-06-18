"Test runner."

import unittest

import api_root
import api_about
import api_user
import api_links
import api_dataset
import api_graphic

loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.loadTestsFromModule(api_root))
suite.addTests(loader.loadTestsFromModule(api_about))
suite.addTests(loader.loadTestsFromModule(api_user))
suite.addTests(loader.loadTestsFromModule(api_links))
suite.addTests(loader.loadTestsFromModule(api_dataset))
suite.addTests(loader.loadTestsFromModule(api_graphic))

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
