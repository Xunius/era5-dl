#!/usr/bin/env python
'''Parse web generated API request and split into small jobs.

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-08 10:10:34.
'''

from __future__ import print_function
from era5dl import batchDownloadFromWebRequest

#--------------Globals------------------------------------------
API_FILE='./examples/test_api1.txt'
OUTPUTDIR = '/home/guangzhi/datasets/era5/newdownload/'
DRY=False




#-------------Main---------------------------------
if __name__=='__main__':

    #batchDownloadFromWebRequest(API_FILE, OUTPUTDIR, ['variable', 'pressure_level', 'year'],
    batchDownloadFromWebRequest(API_FILE, OUTPUTDIR, ['variable', 'year'],
        DRY, pause=3, naming_func=None, verbose=True)
