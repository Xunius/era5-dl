'''Utilities for downloading ECMWF ERA5 reanalysis data.

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-07 11:29:53.
'''

from __future__ import print_function
import os
import copy
import json
import time
import logging
import logging.config
from pprint import pprint
import cdsapi
from .util_general import get1stOrList, toList, getAttrProduct
from . import util_read_param_table
from . import util_request_parser


# logger config
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '<%(filename)s-%(funcName)s()>: %(asctime)s,%(levelname)s: %(message)s'},
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'batch_era5_download.log'
        },
    },
    'loggers': {
        'n1': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

__all__=[
        'retrieveData', 'getLogger', 'skipJobs', 'loadDownloadedList',
        'prepareJobDict', 'prepareBatchJobDicts', 'processJob',
        'processJobs', 'batchDownload', 'batchDownloadFromWebRequest',
        'TEMPLATE_DICT'
        ]

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


def retrieveData(data_target, job_dict, abpath_out, dry=True):
    '''Send cdsapi retrieval request.

    Args:
        data_target (str): target dataset. This is the 1st input arg to the
            cdsapi.Client().retrieve() method.
        job_dict (dict): dictionary describing the data retrieval task.
        abpath_out (str): absolute path to save downloaded data. Create folder if
            not exists already.
    Keyword Args:
        dry (bool): if True, only print the request job without submitting it.

    NOTE that all requirest data are saved into a single file. If data size
    is big, consider break into smaller pieces, using for instance a for-loop.
    '''

    outputdir = os.path.dirname(abpath_out)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    # -------------Run retrieval or dry run-------------
    if dry:
        print('\n########### DRY RUN ############\n')
        print('job_dict = ')
        pprint(job_dict)
        print('data_target = ', data_target)
        print('\nSave file to:', abpath_out)
    else:
        c = cdsapi.Client()
        c.retrieve(data_target, job_dict, abpath_out)

    return


def getLogger(idx, filename, config_base):
    '''Get a new logger for job indexed idx

    Args:
        idx (int): numerical id for the logger.
        filename (str): absolute file path for log file.
        config_base (dict): basic log config to modify.
    Returns:
        logger (logger): logger.
    '''

    logger_name = '%s-%s' % (__name__, str(idx))
    logger_dict = {
        logger_name: {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }}

    config_base['loggers'] = logger_dict
    config_base['handlers']['default']['filename'] = filename
    logging.config.dictConfig(config_base)

    return logging.getLogger(logger_name)


def skipJobs(job_list, skip_list, down_list):
    '''Remove certain jobs from given job list

    Args:
        job_list (list): list of tuples, each defining some aspects of a data
            retrieval task. E.g.
            (('vars', 'u_component_of_wind'), ('years', 1997), ('pressure_levels', 1000))
        skip_list (list): list of tuples, jobs to skip.
        down_list (list): list of tuples, finished jobs.
    Returns:
        result (list): list of tuples, jobs defined in <job_list>, with those
            skipped (in <skip_list) or finished (<down_list>) removed.
    '''

    skip_list2 = []
    for dii in skip_list:
        lii = getAttrProduct(dii)
        skip_list2.extend(lii)

    # skip jobs from down_list
    job1 = job_list[0]
    fields = [ii[0] for ii in job1]

    skip_list3 = []
    for dii in down_list:
        lii = tuple([(kk, dii[kk]) for kk in fields])
        skip_list3.append(lii)

    skip_list2.extend(skip_list3)
    result = list(set(job_list).difference(skip_list2))

    print('\n# <util_downloader>: Number of jobs defined: %d' % len(job_list))
    print(
        '# <util_downloader>: Number of skipped jobs from <skip_list>: %d' %
        len(skip_list2))
    print(
        '# <util_downloader>: Number of already downloaded jobs: %d' %
        len(skip_list3))
    print('# <util_downloader>: Number of jobs after skipping: %d' % len(result))

    return result


def loadDownloadedList(abpath_in):
    '''Load list of downloaded jobs

    Args:
        abpath_in (str): absolute path to the file containing fininished jobs.
    Returns:
        down_list (list): a list of dicts, each defines a downloaded job. This dict
            is the 2nd input arg to the cdsapi.Client().retrieve() method.
    '''

    if os.path.exists(abpath_in):
        try:
            down_list = [json.loads(l) for l in open(abpath_in, 'r')]
        except ValueError:
            down_list = []
    else:
        down_list = []

    return down_list


def prepareJobDict(var_list, years, months, days, hours, time_step, level_type,
                   levels, area=None, out_format='netcdf'):
    '''Prepare retrieval job dictionary.

    Args:
        var_list (list or tuple or str): name(s) of variable(s) to be retrieved.
        years (list or tuple or int): years. E.g. range(1980, 1990).
        months (list or tuple or int): months. E.g. [12, 1, 2].
        days (list or tuple or int): days. E.g. range(1, 31).
        hours (list or tuple or int): hours. E.g. [0, 6, 12, 18].
        time_step (str): 'hourly': for sub-daily resolution, or 'monthly' for
            monthly averages.
        level_type (str): 'p' for pressure level data, 's' for single level data.
        levels (list or tuple or int): pressure levels. Ignored if <level_type>
            is 's'.
    Keyword Args:
        area (list or tuple): domain to retrieve in the format of [N, W, S, E],
            in degrees of latitutde/longitude. If None (default), retrieve
            global data.
        out_format (str): save 'netcdf' (default) or 'grib' format.
    Returns:
        job_dict (dict): dictionary describing the data retrieval task.
        data_target (str): type of data to retrieve. Currently one of

            'reanalysis-era5-single-levels'
            'reanalysis-era5-pressure-levels'
            'reanalysis-era5-single-levels-monthly-means'
            'reanalysis-era5-pressure-levels-monthly-means'

    This function constructs a dictionary ( < job_dict > ) describing a data
    for the retrieval task. This is dict is used as the 2nd input arg to the
    cdsapi.Client().retrieve() method.

    Not too useful.
    '''

    # ------------Convert to list or string------------
    levels = toList(levels)
    levels.sort()
    levels_str = [str(ii) for ii in levels]
    levels_str = get1stOrList(levels_str)

    years = toList(years)
    years_str = [str(ii) for ii in years]
    years_str = get1stOrList(years_str)

    months = toList(months)
    months = [str(ii).rjust(2, '0') for ii in months]
    months = get1stOrList(months)

    var_list = toList(var_list)

    # ------------------Check variable------------------
    varname_tables = util_read_param_table.readAllTables()

    for vv in var_list:
        if level_type == 's':
            valid_names = [
                dd['Variable name in CDS']
                for dd in util_read_param_table.getSurfaceTables(
                    varname_tables)]
        elif level_type == 'p':
            valid_names = varname_tables['table9']['Variable name in CDS']

        if vv not in valid_names:
            raise Exception(
                "Variable %s is not found in table. Double check the variable name." % vv)

    var_list = get1stOrList(var_list)

    if out_format not in ['netcdf', 'grib']:
        raise Exception("<out_format> can be either 'netcdf' or 'grib'.")

    product_type = 'reanalysis' if time_step == 'hourly' else 'monthly_averaged_reanalysis'

    # ----------------Construct job dict----------------
    job_dict = {
        'product_type': product_type,
        'format': out_format,
        'year': years_str,
        'month': months,
        'variable': var_list,
    }

    if level_type == 'p':
        job_dict['pressure_level'] = levels_str

    if time_step == 'hourly':
        days = toList(days)
        days = [str(ii).rjust(2, '0') for ii in days]
        days = get1stOrList(days)
        job_dict['day'] = days

        hours = toList(hours)
        hours = ['%s:00' % (str(ii).rjust(2, '0')) for ii in hours]
        hours = get1stOrList(hours)
    elif time_step == 'monthly':
        hours = '00:00'

    job_dict['time'] = hours

    if area is not None:
        job_dict['area'] = area

    if time_step == 'hourly':
        if level_type == 's':
            data_target = 'reanalysis-era5-single-levels'
        elif level_type == 'p':
            data_target = 'reanalysis-era5-pressure-levels'
    elif time_step == 'monthly':
        if level_type == 's':
            data_target = 'reanalysis-era5-single-levels-monthly-means'
        elif level_type == 'p':
            data_target = 'reanalysis-era5-pressure-levels-monthly-means'

    return job_dict, data_target


def prepareBatchJobDicts(template_dict, job_dict, skip_list, outputdir,
        naming_func=None):
    '''Prepare a list of job dictionaries for a batch download task.

    Args:
        template_dict (dict): default job dict. Relevant fields will be updated
            using corresponding key-value pairs given in <job_dict>.
        job_dict (dict): dict defining the batch download job. Only need to
            provide attributes that are different from the default values
            given in <template_dict>. Other fields will be taken from
            <template_dict>.

            E.g.
            job_dict = {'variable': ['2m_temperature', '10m_u-component_of_wind'],
                'year': range(1979, 1981),
            }

        skip_list (list): list of dicts, each in the same format as <job_dict>.
            This is used to exclude/skip certain jobs.
        outputdir (str): absolute path to the folder to save downloaded data.
    Keyword Args:
        naming_func (callable or None): if a callable, a function that accepts
            a single input argument which a dict (as <template_dict>) defining
            the data retrieval task, and returns a string as the filename
            (without folder path) to name the downloaded data. If None,
            construct a default filename, using the following format:
                [ID<n>]<attributes>.nc or
                [ID<n>]<attributes>.grb

            where <n> is the numerical id of the job, <attributes> is a
            dash concatenated string joining the attributes that define the job.
            E.g.
                [ID02]700-geopotential-2000.nc
    Returns:
        result (list): a list of dicts, each defines a download job. This dict
            is the 2nd input arg to the cdsapi.Client().retrieve() method.
    '''

    # try get downloaded jobs
    down_list_file = os.path.join(outputdir, 'downloaded_list.txt')
    down_list = loadDownloadedList(down_list_file)

    # form imcomplete job dicts
    jobs = getAttrProduct(job_dict)
    jobs = skipJobs(jobs, skip_list, down_list)
    jobs = [dict(ii) for ii in jobs]

    result = []
    for ii, jobii in enumerate(jobs):

        # get the complete job dict: tmpdictii
        jobid = str(ii).rjust(len(str(len(jobs))), '0')
        tmpdictii = copy.deepcopy(template_dict)
        tmpdictii.update(jobii)

        # ---------------Get output file name---------------
        if naming_func is None:
            keys = list(jobii.keys())
            keys.sort()
            values = [jobii[kk] for kk in keys]
            fileout_name = '[ID%s]%s%s' % (
                jobid, '-'.join(map(str, values)),
                '.nc' if tmpdictii['format'] == 'netcdf' else '.grb')
        else:
            fileout_name = naming_func(tmpdictii)

        abpath_out = os.path.join(outputdir, fileout_name)
        tmpdictii['abpath_out'] = abpath_out

        result.append(tmpdictii)

    return result


def processJob(job_dict, jobid, outputdir, dry):
    '''Process a data retrieval job

    Args:
        job_dict (dict): dict defining a download job. This dict
            is the 2nd input arg to the cdsapi.Client().retrieve() method.
        jobid (str): id of the job.
        outputdir (str): absolute path to the folder to save downloaded data.
        dry (bool): if True, only print the request job without submitting it.

    Function logs the job info to a log file in the specified output directory
    (<outputdir>), and calls the retrieveData() to retrieve data, or simulate
    a dry run.
    '''

    # ---------------Get a logger for job---------------
    logger = getLogger( 'root', os.path.join( outputdir, 'era5_downloader.log'),
        LOG_CONFIG)

    # ---------------------Retrieve---------------------
    data_target = job_dict.pop('data_target')
    abpath_out = job_dict.pop('abpath_out')

    logger.info('<batch_download>: Output folder at: %s' % outputdir)
    logger.info('Launch job %s' % jobid)
    logger.info('Job info: %s' % (str(job_dict)))
    logger.info('Output file location: %s' % abpath_out)

    retrieveData(data_target, job_dict, abpath_out, dry=dry)

    return


def processJobs(job_dicts, outputdir, dry, pause=3, verbose=True):
    '''Process multiple data retrieval jobs

    Args:
        job_dicts (list): a list of dicts, each defines a download job. This dict
            is the 2nd input arg to the cdsapi.Client().retrieve() method.
        outputdir (str): absolute path to the folder to save downloaded data.
        dry (bool): if True, only print the request job without submitting it.
    Keyword Args:
        pause (int): number of seconds to pause between jobs.
    '''

    if len(job_dicts) == 0:
        print('\n# <batch_download>: No job to run.')
    else:
        fail_list = []
        done_list = []
        down_list_file = os.path.join(outputdir, 'downloaded_list.txt')

        for ii, jobii in enumerate(job_dicts):

            idstr = str(ii+1).rjust(len(str(len(job_dicts))), '0')
            print('\n# <batch_download>: Processing job %s/%d\n' %(idstr, len(job_dicts)))

            try:
                processJob(jobii, idstr, outputdir, dry)
            except Exception as e:
                print('Failed job %s.' %idstr, e)
                fail_list.append(jobii)
            else:
                if not dry:
                    done_list.append(jobii)
                    with open(down_list_file, 'a') as down_fout:
                        json.dump(jobii, down_fout)
                        down_fout.write('\n')

                time.sleep(pause)

        # ------------------Print summary------------------
        if len(fail_list) == 0:
            print('\n# <batch_download>: All done.')
        else:
            print('\n# <batch_download>: Failed jobs:')

            for ii in fail_list:
                print(ii)

    return


def batchDownload(template_dict, job_dict, skip_list, outputdir, dry, pause=3,
                  naming_func=None, verbose=True):
    '''Start a batch downloading job

    Args:
        template_dict (dict): default job dict. Relevant fields will be updated
            by corresponding key-value pairs in given in <job_dict>.
        job_dict (dict): dict defining the batch download job. Only need to
            provide attributes that are different from the default template
            given in TEMPLATE_DICT. Other fields will be taken from TEMPLATE_DICT.

            E.g.
            job_dict = {
                'variable': ['2m_temperature', '10m_u-component_of_wind'],
                'year': range(1979, 1981),
            }
        skip_list (list): list of dicts, each in the same format as <job_dict>.
            This is used to exclude/skip certain jobs.
        outputdir (str): absolute path to the folder to save downloaded data.
        dry (bool): if True, only print the request job without submitting it.
    Keyword Args:
        pause (int): number of seconds to pause between jobs.
        naming_func (callable or None): if a callable, a function that accepts
            a single input argument which a dict (as <template_dict>) defining
            the data retrieval task, and returns a string as the filename
            (without folder path) to name the downloaded data. If None,
            construct a default filename, using the following format:
                [ID<n>]<attributes>.nc or
                [ID<n>]<attributes>.grb

            where <n> is the numerical id of the job, <attributes> is a
            dash concatenated string joining the attributes that define the job.
            E.g.
                [ID02]700-geopotential-2000.nc
    '''

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
        print('\n# <batch_download>: Create folder at: %s' % outputdir)

    jobs = prepareBatchJobDicts(template_dict, job_dict, skip_list, outputdir,
                                naming_func=naming_func)
    processJobs(jobs, outputdir, dry, pause, verbose)

    return


def batchDownloadFromWebRequest(request_file, outputdir, split_fields, dry,
        pause=3, naming_func=None, verbose=True):
    '''Start a batch downloading job split from a web api request

    Args:
        request_file (str): absolute path to a text file containing the data
            retrieval task obtained from the CDS web interface.
        outputdir (str): absolute path to the folder to save downloaded data.
        split_fields (list or tuple): dimensions along which to split the job
            into sub-jobs. E.g. ['variable', 'year', 'pressure_level'] will
            split the retrieval job into a number of sub-jobs such that each
            one retrieves one variable, in one year, on each pressure level.
            If 'variable'=['u', 'v'], 'year'=[1999, 2000], 'pressure_level'=
            [900, 950, 1000], this will create 2x2x3 = 12 sub-jobs, starting
            with ('variable'='u', 'year'=1999, 'pressure_level'=900).
        dry (bool): if True, only print the request job without submitting it.
    Keyword Args:
        pause (int): number of seconds to pause between jobs.
        naming_func (callable or None): if a callable, a function that accepts
            a single input argument which a dict (as <template_dict>) defining
            the data retrieval task, and returns a string as the filename
            (without folder path) to name the downloaded data. If None,
            construct a default filename, using the following format:
                [ID<n>]<attributes>.nc or
                [ID<n>]<attributes>.grb

            where <n> is the numerical id of the job, <attributes> is a
            dash concatenated string joining the attributes that define the job.
            E.g.
                [ID02]700-geopotential-2000.nc
    '''

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
        print('\n# <batch_download>: Create folder at: %s' % outputdir)

    template_dict = util_request_parser.parseFile(request_file)

    # split jobs
    #jobs=util_request_parser.splitBy(job_dict, split_fields)
    job_dict = dict([(kk, template_dict[kk]) for kk in split_fields])

    jobs = prepareBatchJobDicts(template_dict, job_dict, [], outputdir,
                                naming_func=naming_func)
    processJobs(jobs, outputdir, dry, pause, verbose)

    return
