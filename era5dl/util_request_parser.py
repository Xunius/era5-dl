'''Functions for parse web generated API request and split into small jobs.

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-08 10:10:34.
'''

from __future__ import print_function
import os
import re
import copy
from pprint import pprint
from .util_general import getAttrProduct

__all__=[
        'DATA_TARGET_PATTERN', 'DICT_PATTERN', 'DICT_KEY_VALUE_PATTERN',
        'parseJobDict', 'splitBy', 'parseFile', 'parseString'
        ]

#------------api request parsing regex------------
DATA_TARGET_PATTERN=re.compile(r'''
^c\.retrieve\(  # start of the retrieve() function
\s*'(.*?)',     # next line
''', re.MULTILINE | re.VERBOSE)

DICT_PATTERN=re.compile(r"^\s*\{(.*)\},", re.DOTALL | re.MULTILINE)

#DICT_KEY_VALUE_PATTERN=re.compile(r"^\s*'(\w+)':\s*(.*?)(?=^\s*'(?:\w+)':|\Z)", re.DOTALL | re.MULTILINE)
DICT_KEY_VALUE_PATTERN=re.compile(r'''
^\s*'(\w+)':            # key, e.g. 'variable':
\s*                     # space
(.*?)                   # value, e.g. 'netcdf', '[\n   '1991', '1992', '1993',\n],
(?=^\s*'(?:\w+)':|\Z)   # non-capturing lookfoward, could be a new key, e.g.
                        # 'year', or the end of the string for the last
                        # key-value pair
''', re.DOTALL | re.MULTILINE | re.VERBOSE)


def parseJobDict(job_list):
    '''Put list of key-value pairs into a dict

    Args:
        job_list (list): list of (key, value) pairs, where <value> is an
            unformatted string, which has to be converted to a normal string,
            or list, using eval(value).
    Returns:
        result (dict): dict containing all key-value pairs in <job_list>.
    '''

    result={}
    for ii, (kii, vii) in enumerate(job_list):
        vii=vii.strip().strip(',')
        valueii=eval(vii)
        result[str(kii)]=valueii

    return result

def splitBy(job_dict, split_fields, verbose=True):
    '''Split total request job into a number of sub-jobs

    Args:
        job_dict (dict): parsed dictionary defining a data retrieval request job.
        split_fields (list or tuple): dimensions along which to split the job
            into sub-jobs. E.g. ['variable', 'year', 'pressure_level'] will
            split the retrieval job into a number of sub-jobs such that each
            one retrieves one variable, in one year, on each pressure level.
            If 'variable'=['u', 'v'], 'year'=[1999, 2000], 'pressure_level'=
            [900, 950, 1000], this will create 2x2x3 = 12 sub-jobs, starting
            with ('variable'='u', 'year'=1999, 'pressure_level'=900).
    Returns:
        results (list): list of dicts, each defines a sub-job retrieval.
    '''

    keys=job_dict.keys()
    split_dims={}
    for kii in split_fields:
        if kii not in keys:
            raise Exception("Key '%s' not in <job_dict>." %kii)

        # don't split area
        if kii in ['area',]:
            if verbose:
                print('\n# <splitBy>: Skip "%s"' %kii)

        split_dims[kii]=job_dict[kii]

    sub_jobs=getAttrProduct(split_dims)
    results=[]
    for jobii in sub_jobs:
        jobii=dict(jobii)
        dictii=copy.deepcopy(job_dict)
        dictii.update(dict(jobii))
        results.append(dictii)

    if verbose:
        print('\n# <splitBy>: Splited job by', split_fields)
        print('# <splitBy>: Number of sub-jobs = %d' %(len(results)))

    return results

def parseFile(abpath_in, verbose=True):
    '''Parse a web generated API request saved in a file

    Args:
        abpath_in (str): absolute path to the text file saving the API request.
    Returns:
        job_dict (dict): a dictionary defining the data retrieval task. This
            is the same form as the 2nd input argument to the
            cdsapi.Client().retrieve() method.
    '''

    with open(abpath_in, 'r') as fin:
        lines=fin.readlines()
        if len(lines)==0:
            raise Exception("File %s is empty." %abpath_in)
        lines=''.join(lines)

    return parseString(lines, verbose)

def parseString(lines, verbose=True):
    '''Parse a web generated API request in a string

    Args:
        lines (str): API request in string format.
    Returns:
        job_dict (dict): a dictionary defining the data retrieval task. This
            is the same form as the 2nd input argument to the
            cdsapi.Client().retrieve() method.
    '''

    try:
        data_target=DATA_TARGET_PATTERN.search(lines).group(1)
    except:
        raise Exception("DATA_TARGET_PATTERN failed to match the string.")

    try:
        job_dict_str=DICT_PATTERN.search(lines).group(1)
    except:
        raise Exception("DICT_PATTERN failed to match the string.")

    try:
        job_dict_pairs=DICT_KEY_VALUE_PATTERN.findall(job_dict_str)
    except:
        raise Exception("DICT_KEY_VALUE_PATTERN failed to match the string.")

    job_dict=parseJobDict(job_dict_pairs)
    job_dict['data_target']=data_target

    return job_dict




#-------------Main---------------------------------
if __name__=='__main__':

    API_FILE='../examples/test_api1.txt'
    OUTPUTDIR='.'

    api_file=os.path.abspath(API_FILE)
    job_dict=parseFile(api_file)
    pprint(job_dict)

    # split jobs
    split_jobs=splitBy(job_dict, OUTPUTDIR, ['variable', 'pressure_level', 'year'])









