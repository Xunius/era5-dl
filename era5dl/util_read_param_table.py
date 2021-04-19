'''Functions for reading ERA5 parameter table info saved in csv format.

Author: guangzhi XU (xugzhi1987@gmail.com)
Update time: 2021-04-09 11:13:20.
'''

from __future__ import print_function
import os
import glob
import csv

TABLE_FOLDER=os.path.abspath(os.path.join(os.path.abspath(__file__), '../tables/'))


def readTable(abpath_in, verbose=True):
    '''Read in a table from a csv file and return table in dict format

    Args:
        abpath_in (str): absolute path to csv file.
    Returns:
        result (dict): table stored in a dict. Keys: table columns. Values:
            a list of column values corresponding to a given header.
    '''

    result={}
    with open(abpath_in, 'r') as fin:
        reader=csv.reader(fin, delimiter=',')
        header=reader.__next__()
        for kii in header:
            result[kii]=[]

        for lii in reader:
            for jj, vjj in enumerate(lii):
                result[header[jj]].append(vjj)

    return result

def queryField(table, target_column, given_column, given_value, verbose=True):
    '''Query from a table a target value in a target column

    Args:
        table (dict): table stored in a dict. Keys: table columns. Values:
            a list of column values corresponding to a given header.
        target_column (str): header name of the target value, defines the column
            of the target value to query.
        given_column (str): header name of the given value, defines the column
            of the given value.
        given_value (str): defines the row of the target value. Note that the
            given_value needs to be able to uniquely define a row.
    Returns:
        result (str): target value, at the row defined by <given_value>, in
            the column specified by <target_column>.
    '''

    if target_column not in table:
        raise Exception("<target_column> '%s' not in <table>.\nAll columns: %s" %(target_column, table.keys()))
    if given_column not in table:
        raise Exception("<given_column> '%s' not in <table>.\nAll columns: %s" %(given_column, table.keys()))

    target_values=table[target_column]
    given_values=table[given_column]
    try:
        idx=given_values.index(given_value)
    except Exception as e:
        raise Exception("<given_value> not found:", e)

    if given_values.count(given_value)>1:
        raise Exception("<given_value> '%s' does not uniquely define a row in <table>." %given_value)

    result=target_values[idx]

    return result

def readAllTables():
    '''Read all tables'''

    table_files=glob.glob(os.path.join(TABLE_FOLDER, 'table*.csv'))
    table_files.sort()
    table_dict={}
    for fii in table_files:
        tableii=readTable(fii)
        nameii=os.path.basename(fii).split('.')[0]
        table_dict[nameii]=tableii

    return table_dict

def getSurfaceTables(all_tables):
    '''Get only tables for surface/single level parameters'''
    return [all_tables['table%d' %ii] for ii in range(1,7)]

def getShortNames(*args):
    '''Get shortName from Variable name in CDS

    Args:
        *args (tuple): tuple of strings, Variable name in CDS.
    Returns:
        results (str or list): corresponding ShortName (e.g. 'z', 't') for each
            variable name in <*args>, ('geopotential', 'temperature').
    '''

    results=[]
    all_tables=readAllTables()

    for vii in args:
        for kjj,tjj in all_tables.items():
            try:
                shortnameii=queryField(tjj, 'shortName', 'Variable name in CDS', vii)
            except:
                shortnameii=vii
            else:
                break
        results.append(shortnameii)

    if len(results)==1:
        return results[0]
    else:
        return results


if __name__=='__main__':

    TABLES=readAllTables()
    a=getShortNames('geopotential', 'divergence', 'relative_humidity', 'runoff', 'aaa')








