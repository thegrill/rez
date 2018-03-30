"""Main entry point"""

import sys
if sys.argv[0].endswith("__main__.py"):
    sys.argv[0] = "unittest2"

__unittest = True

import unittest.main as main_
main_()
