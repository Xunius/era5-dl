#!/usr/bin/env python
'''Script for downloading ERA5 reanalysis data in small amounts.

For large data amount download in batch mode, see batch_download.py.

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-07 11:33:10.
'''

import os
from era5dl import prepareJobDict, retrieveData

# -----------------Data to retrieve-----------------
DRY = True
VARS = ['u_component_of_wind', 'geopotential']
YEARS = range(1979, 1981)
MONTHS = [1, 2]
DAYS = range(1, 3)
HOURS = [0, 6, 12, 18]
TIME_STEP = 'hourly'    # 'hourly' | 'monthly'
LEVEL_TYPE = 'p'   # 'p', 's'
LEVELS = [1000, 975, 950, 925, 900, 875, 850, 825, 800, 775, 750,
          700, 650, 600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100, 50]
LEVELS = [1000, 975, 950, 925, 900]
AREA = None  # N, W, S, E
AREA = [10, 0, 0, 10]  # N, W, S, E
FORMAT = 'netcdf'


OUTPUTDIR = './'


if __name__ == '__main__':

    job_dict, data_target = prepareJobDict(
        VARS, YEARS, MONTHS, DAYS, HOURS, TIME_STEP, LEVEL_TYPE, LEVELS,
        area=AREA, out_format=FORMAT)
    fileout_name = 'era5_download.%s' % 'era5.nc' if FORMAT == 'netcdf' else 'era5.grb'
    abpath_out = os.path.join(OUTPUTDIR, fileout_name)
    retrieveData(data_target, job_dict, abpath_out, dry=DRY)
