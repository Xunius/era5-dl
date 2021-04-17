'''General utility functions

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-17 08:36:48.
'''

from __future__ import print_function
import os
import re

def isListTuple(x):
    """Check an input is a list or tuple or range

    Args:
        x (unknow type): input
    Returns:
        True if <x> is list, tuple or range type, False otherwise.
    """
    import sys

    if sys.version_info.major == 2:
        return isinstance(x, (list, tuple))
    else:
        return isinstance(x, (list, tuple, range))


def get1stOrList(a):
    '''Cast input into a list, or return its 1st element'''
    if len(a) == 1:
        return a[0]
    else:
        return list(a)


def toList(x):
    '''Put input into a list if not already a list'''
    if not isListTuple(x):
        return [x, ]
    else:
        return x


def autoRename(abpath):
    '''Auto rename a file to avoid overwriting an existing file

    <abpath>: str, absolute path to a folder or a file to rename.

    Return <newname>: str, new file path.
    If no conflict found, return <abpath>;
    If conflict with existing file, return renamed file path,
    by appending "_(n)".
    E.g.
        n1='~/codes/tools/send2ever.py'
        n2='~/codes/tools/send2ever_(4).py'
    will be renamed to
        n1='~/codes/tools/send2ever_(1).py'
        n2='~/codes/tools/send2ever_(5).py'
    '''

    def rename_sub(match):
        base = match.group(1)
        delim = match.group(2)
        num = int(match.group(3))
        return '%s%s(%d)' % (base, delim, num+1)

    if not os.path.exists(abpath):
        return abpath

    folder, filename = os.path.split(abpath)
    basename, ext = os.path.splitext(filename)
    # match filename
    rename_re = re.compile('''
            ^(.+?)       # File name
            ([- _])      # delimiter between file name and number
            \\((\\d+)\\) # number in ()
            $''',
                           re.X)

    newname = '%s_(1)%s' % (basename, ext)
    while True:
        newpath = os.path.join(folder, newname)

        if not os.path.exists(newpath):
            break
        else:
            if rename_re.match(newname):
                newname = rename_re.sub(rename_sub, newname)
                newname = '%s%s' % (newname, ext)
            else:
                raise Exception("Exception")

    newname = os.path.join(folder, newname)
    return newname


def getAttrProduct(job_dict):
    '''Create combinations of multiple attributes.

    Args:
        job_dict (dict): dict containing attributes to iterate through.
    Returns:
        result2 (list): list of dicts containing combinations of attributes from
            <job_dict>.
            E.g. job_dict = {'vars' : ['u', 'v'],
                             'years' : [1997, 1998],
                             'levels' : [1000, 900, 800]}
                result2 will be:
                    [{'vars': 'u', 'years': 1997, 'levels': 1000},
                     {'vars': 'u', 'years': 1997, 'levels': 900},
                     {'vars': 'u', 'years': 1997, 'levels': 800},
                     {'vars': 'u', 'years': 1998, 'levels': 1000},
                     {'vars': 'u', 'years': 1998, 'levels': 900},
                     {'vars': 'u', 'years': 1998, 'levels': 800},
                     {'vars': 'v', 'years': 1997, 'levels': 1000},
                     ...
                     {'vars': 'v', 'years': 1998, 'levels': 800}
                     ]
    '''

    pools = [(v,) if not isListTuple(v) else tuple(v)
             for v in job_dict.values()]

    # -----------------Get combinations-----------------
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]

    result2 = []
    keys = job_dict.keys()
    for ii, jobii in enumerate(result):
        dii = tuple(zip(keys, jobii))
        result2.append(dii)

    return result2

