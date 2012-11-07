# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import os
import sys
import csv
import pandas
import logging

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

import etl
from share import Config
from share import parallel_jobs
from share import Stark

COLUMNS = [
    'R', 
    'YEAR', 
    'CODE',
    'XER',
    'MER', 
    'X', 
    'M', 
    'K', 
    'U',
    'Q']

DIMENSIONS = ['XER', 'MER', 'YEAR', 'R', 'CODE']

# TODO: evaluate from meta
STRUCT_PROD = ['UL20', 'UL200', 'UL1000', 'UL3000']
STRUCT_COUNTRY = ['area', 'country', 'region', 'province']
AGGR_LVL = 'UL1000'

_logger = logging.getLogger(sys.argv[0])

def _list_files(level, root):
    ''' Make a list of files at a given level of directory nesting, starting
    from root.
    
    @ param level: the nesting level to search
    @ param root: the directories tree root
    @ return: a list of paths
    '''
    out = []
    found = (root, [], [])
    for name in os.listdir(root):
        fullname = os.path.join(root, name)
        if os.path.isfile(fullname):
            found[2].append(fullname)
        elif os.path.isdir(fullname):
            found[1].append(fullname)
    curr, dirs, files = found
    if level <= 0:
        # Target level reached
        out.extend(files)
    else:
        for dir_ in dirs:
            out.extend(_list_files(level-1, dir_))
    return out

def by_country(level, in_path, root, mapping):
    ''' Reshape DataFrames classified by product code into DataFrame organized
    by country (ISO3 code). A product aggregation level can be specified.
    
    @ param level: product code aggregation level
    @ param in_path: input files root path
    @ param root: output root path
    @ mapping: ISO3 code mapping DataFrame
    '''
    files = _list_files(STRUCT_PROD.index(level), in_path)
    # Make sure mapping is indicized by country
    mapping = mapping.reset_index().set_index('ISO3', drop=True)['AREA']
    for country in mapping.index:
        _logger.info('Aggregating by %s', country)
        out_df = pandas.DataFrame(columns=COLUMNS)
        area = mapping.ix[country].replace(' ', '_')
        filename = '.'.join([country, 'pickle'])
        fullpath = os.path.join(root, area, filename)
        for file_ in files:
            try:
                df = pandas.load(file_).groupby('XER').get_group(country).reset_index()
            except KeyError:
                # Country not present in the current df
                continue
            out_df = out_df.append(df, ignore_index=True, verify_integrity=False)
            out_df = out_df.groupby(DIMENSIONS).sum()
        _logger.debug('Writing %s', fullpath)
        # If output path does not exists, create it
        if not os.path.isdir(os.path.dirname(fullpath)):
            os.makedirs(os.path.dirname(fullpath))
        out_df.save(fullpath)

def _from_hs(level, in_path, root, code, group):
    ''' Aggregate form HS6digit into Ulisse classification.

    @ param level: aggregation level
    @ param in_path: list of input files
    @ param root: root directory for output
    @ param code: target product code
    @ param group: other code converging into code.
    '''
    _logger.info('Processing %s', code)
    df_out = pandas.DataFrame(columns=COLUMNS)
    for hs in group['HS07']:
        try:
            df = pandas.load(os.path.join(in_path, '.'.join([hs, 'pickle'])))
        except IOError:
            # File does not exists
            continue
        df['CODE'] = len(df) * [code]
        df.consolidate(inplace=True) # Should reduce memory usage
        # TODO: Handle non summable quantities
        df_out = df_out.append(df[COLUMNS], ignore_index=True, verify_integrity=False)
        df_out = df_out.groupby(DIMENSIONS).sum().reset_index()
    try:
        path = group[STRUCT_PROD[:STRUCT_PROD.index(level)]].ix[group.index[0]].tolist()
    except IndexError:
        # empty group
        return
    path.insert(0, root)
    path.append(code)
    filename = '.'.join([os.path.join(*path), 'pickle'])
    # If output path does not exists, create it
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    df_out.save(filename)

def from_hs(level, in_path, root, prod_map):
    ''' Convert DataFrames from HS6digit classification to Ulisse
    classification.

    This is just a wrapper to run the conversion with multiple processes. See
    _from_hs() for the aggregation algorithm.

    @ param level: aggregation level
    @ param in_path: list of input files
    @ param root: root directory for output
    @ param prod_map: product codes mapping DataFrame
    ''' 
    # TODO: use Starks!
    prod_groups = prod_map.groupby(level)
    args = [(_from_hs, [level, in_path, root, code, group]) for code, group in prod_groups]
    parallel_jobs.do_jobs_efficiently(args)
        
def aggregate(root, mapping, struct=None):
    ''' Aggregates DataFrames stored in Python pickle files. This function
    performs a bottom-up walk of a directory subtree, aggregating DataFrames in
    each directory and storing the resulting DataFrame in the parent folder.

    @ param root: output root dir
    @ param mapping: product codes mapping DataFrame
    '''
    walker = os.walk(root, topdown=False)
    if struct is None:
        struct = STRUCT_PROD
    for current, dirs, files in walker:
        if len(files) == 0:
            # XXX: Cludgy workaround to os.walk() behaviour: when doing a bottom-up
            # search, files generated during iteration are not found because the
            # iteration itself is subsequent to a depth-first walk through the
            # directory tree; files are not listed when the algorithm yields a
            # parent node, but when it reach it in the initial depth-first
            # walk.
            for fname in os.listdir(current):
                if os.path.isfile(os.path.join(current, fname)):
                    files.append(fname)
        out_code = os.path.split(current)[1]
        _logger.info('Aggregating by %s', out_code)
        out_file = '.'.join([out_code, 'pickle'])
        level_name = ''
        prev_level_name = ''
        for idx, name in enumerate(struct):
            if len(mapping.ix[mapping[name] == out_code]) > 0:
                level_name = name
                prev_level_name = struct[idx + 1]
                break
        df_out = pandas.DataFrame(columns=COLUMNS)
        # Select the mapping informations strictly needed for the current
        # aggregation. Merging with unnecessary data is a huge memory sink
        curr_mapping = mapping.groupby(level_name).get_group(out_code)
        curr_mapping = curr_mapping[[level_name, prev_level_name]].drop_duplicates()
        # Aggregate files
        for file_ in files:
            if struct is STRUCT_PROD:
                fk = 'CODE'
            elif struct is STRUCT_COUNTRY:
                fk = 'XER'
            else: # pragma: no cover
                raise ValueError("Struct must be one of (STRUCT_PROD | STRUCT_COUNTRY)")
            df = pandas.load(os.path.join(current, file_))
            df = df.merge(curr_mapping, left_on=fk, right_on=prev_level_name)
            # Drop old CODE and substitute with new one
            if struct is STRUCT_PROD:
                del df[fk]
                df.rename(columns={level_name: fk}, inplace=True)
            # TODO: check if it's needed
            #df.consolidate(inplace=True)
            df_out = df_out.append(df[COLUMNS], ignore_index=True, verify_integrity=False)
            df_out = df_out.groupby(DIMENSIONS).sum().reset_index()
        full_path = os.path.join(current, os.path.pardir, out_file)
        _logger.debug('Saving %s', full_path)
        df_out.save(full_path)

def init(input_dir, ulisse_codes, countries, ums):
    """ Init environment:
    - UL3000 mapping
    - country list
    - input file list
    """
    ul3000 = pandas.DataFrame.from_csv(ulisse_codes).reset_index()
    ums_df = pandas.DataFrame.from_csv(ums).reset_index()
    country_map = pandas.DataFrame.from_csv(countries).reset_index()
    file_list = [os.path.join(input_dir, file_)
                 for file_ in os.walk(input_dir).next()[2]]
    return (file_list, country_map, ul3000, ums_df)

def main(input_dir=None, root=None, start_year=None,
         countries=None, ulisse_codes=None, ums=None, 
         meta=None, product_tree=None, country_tree=None, 
         **kwargs):
    """
    Main procedure:
    """

    # pivot by contry
    file_list, country_map, ul3000, ums_df = init(input_dir, ulisse_codes, countries, ums)

    # Transform by UL codes and aggregate
    ul_root = os.path.join(root, 'prod')
    from_hs('UL3000', input_dir, ul_root, ul3000)
    aggregate(ul_root, ul3000)
 
    # Transform by ISO3 code and aggregate
    iso3_root = os.path.join(root, 'country')
    by_country('UL1000', ul_root, iso3_root, country_map)
    aggregate(iso3_root, country_mapping, struct=STRUCT_CONTRY)
    
    return 0


if __name__ == '__main__':
    config = Config(os.path.join(BASEPATH, 'config/ercole/ercole_sort.cfg'))
    config.parse()
    _logger = logging.getLogger(sys.argv[0])
    sys.exit(main(**config.options))
