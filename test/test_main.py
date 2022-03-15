import unittest
import sys
import os
sys.path.append(os.path.abspath(
    os.path.join(__file__, "../../src")
))


if __name__ == '__main__':
    testsuite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner(verbosity=1).run(testsuite)