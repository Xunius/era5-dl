#!/usr/bin/env python
'''Batch download data from ERA5 reanalysis.

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-07 15:10:42.
'''

from __future__ import print_function
from era5dl import batchDownload


# -----------------------Jobs-----------------------
OUTPUTDIR = './'


JOB_DICT = {
    'variable': ['2m_temperature', '10m_u-component_of_wind'],
    'year': range(1979, 1981),
}

SKIP_LIST = [
    {'variable': '10m_u-component_of_wind', 'year': [1980, ]},
    {'variable': '2m_temperature', 'year': [1979, ]},
]

JOB_DICT = {
    'variable': ['u_component_of_wind', 'geopotential'],
    'year': range(2000, 2002),
    'pressure_level': [1000, 800]
}

SKIP_LIST = [
    {'variable': 'u_component_of_wind', 'year': [2000, ], 'pressure_level': [1000, 800]},
    {'variable': 'geopotential', 'year': [2001, ], 'pressure_level': [800, ]}, ]


TEMPLATE_DICT = {
    'data_target': 'reanalysis-era5-pressure-levels',
    'product_type': 'reanalysis',
    'format': 'netcdf',
    'variable': [
        'geopotential', 'specific_humidity',
    ],
    'pressure_level': [
        '300', '500', '700',
    ],
    'year': [
        '1991', '1992', '1993',
    ],
    'month': [
        '01', '02', '03',
        '04', '05', '06',
        '07', '08', '09',
        '10', '11', '12',
    ],
    'day': [
        '01', '02', '03',
        '04', '05', '06',
        '07', '08', '09',
        '10', '11', '12',
        '13', '14', '15',
        '16', '17', '18',
        '19', '20', '21',
        '22', '23', '24',
        '25', '26', '27',
        '28', '29', '30',
        '31',
    ],
    'time': [
        '00:00', '06:00', '12:00',
        '18:00',
    ],
    'area': [10, 80, -10, 100],
}

if __name__ == '__main__':

    batchDownload(TEMPLATE_DICT, JOB_DICT, SKIP_LIST, OUTPUTDIR, dry=False, pause=3)
