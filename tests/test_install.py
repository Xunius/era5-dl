'''Test installation.
'''

from __future__ import print_function
import unittest

class TestERA5dl(unittest.TestCase):

    def test_era5dl(self):

        from era5dl import util_downloader, util_request_parser, util_general,\
                util_read_param_table, __version__
        print('era5dl version:', __version__)

if __name__=='__main__':

    unittest.main()



