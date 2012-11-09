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

COLUMNS = ['YEAR', 'CODE', 'XER', 'MER', 'R', 'X', 'M', 'K', 'U', 'Q']
META = {
    'YEAR': {'TIP': 'D'},
    'CODE': {'TIP': 'D'},
    'XER': {'TIP': 'D'},
    'MER': {'TIP': 'D'},
    'R': {'TIP': 'D'},
    'X': {'TIP': 'N'},
    'M': {'TIP': 'N'},
    'K': {'TIP': 'N'},
    'U': {'TIP': 'N'},
    'Q': {'TIP': 'N'},
}

STRUCT_PROD = ('UL20', 'UL200', 'UL1000', 'UL3000')
STRUCT_COUNTRY = ('AREA', 'ISO3')
PRIMARYK = {STRUCT_PROD: 'CODE', STRUCT_COUNTRY: 'XER'}

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

def _by_country(root, mapping, country, group):
    stark_group = Stark(group, META)
    try:
        area = mapping.ix[country].replace(' ', '_')
    except KeyError:
        return
    out_file = os.path.join(root, area, '.'.join([country, 'pickle']))
    if not os.path.isfile(out_file):
        stark_out = Stark(pandas.DataFrame(columns=COLUMNS), META)
    else:
        stark_out = Stark.load(out_file)
    stark_out += stark_group
    if not os.path.isdir(os.path.dirname(out_file)):
        os.makedirs(os.path.dirname(out_file))
    stark_out.save(out_file)

def by_country(level, in_path, root, mapping):
    ''' Reshape DataFrames classified by product code into DataFrame organized
    by country (ISO3 code). A product aggregation level can be specified.
    
    @ param level: product code aggregation level
    @ param in_path: input files root path
    @ param root: output root path
    @ mapping: ISO3 code mapping DataFrame
    '''
    # Make sure mapping is indicized by country
    mapping = mapping.reset_index().set_index('ISO3', drop=True)['AREA']
    files = _list_files(STRUCT_PROD.index(level), in_path)
    for idx, file_ in enumerate(files):
        _logger.info('Inspecting file %s: %s', idx, file_)
        stark_curr = Stark.load(file_)
        
        if _logger.getEffectiveLevel() <= logging.DEBUG:
            for country, group in stark_curr.DF.groupby('XER'):
                _by_country(root, mapping, country, group)
        else:
            args = [(_by_country, [root, mapping, country, group])
                    for country, group in stark_curr.DF.groupby('XER')]
            parallel_jobs.do_jobs_efficiently(args)

def _from_hs(level, in_path, root, code, group):
    ''' Aggregate form HS6digit into Ulisse classification.

    @ param level: aggregation level
    @ param in_path: list of input files
    @ param root: root directory for output
    @ param code: target product code
    @ param group: other code converging into code.
    '''
    _logger.info('Aggregating by %s', code)
    df_out = pandas.DataFrame(columns=COLUMNS)
    stark_out = Stark(df_out, META)
    # Make the aggregation
    for hs in group['HS07']:
        try:
            df = pandas.load(os.path.join(in_path, '.'.join([hs, 'pickle'])))
        except IOError:
            # File does not exists
            continue
        df['CODE'] = len(df) * [code]
        df.consolidate(inplace=True) # Should reduce memory usage
        stark_tmp = Stark(df, META)
        stark_out += stark_tmp
    # Handle out path
    try:
        path = group[list(STRUCT_PROD[:STRUCT_PROD.index(level)])].ix[group.index[0]].tolist()
    except IndexError:
        # empty group
        return
    path.insert(0, root)
    path.append(code)
    filename = '.'.join([os.path.join(*path), 'pickle'])
    # If output path does not exists, create it
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    _logger.debug('Saving %s', filename)
    stark_out.save(filename)

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
    prod_groups = prod_map.groupby(level)
    if _logger.getEffectiveLevel() <= logging.DEBUG:
        for code, group in prod_groups:
            _from_hs(level, in_path, root, code, group)
    else:
        args = [(_from_hs, [level, in_path, root, code, group]) for code, group in prod_groups]
        parallel_jobs.do_jobs_efficiently(args)
        
def _total(root, files):
    ''' 
    '''
    stark_out = Stark(pandas.DataFrame(columns=COLUMNS), META)
    for file_ in files:
        stark_tmp = Stark.load(os.path.join(root, file_))
        stark_out += stark_tmp
    filename = '_'.join([os.path.basename(root), 'TOT.pickle'])
    stark_out.save(os.path.join(root, os.path.pardir, filename))

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
            # exploration.
            for fname in os.listdir(current):
                if os.path.isfile(os.path.join(current, fname)):
                    files.append(fname)
        if current == root:
            # root reached: evaluate total and exit
            _total(root, files)
            return
        out_code = os.path.split(current)[1]
        _logger.info('Aggregating by %s', out_code)
        out_file = '.'.join([out_code, 'pickle'])
        level_name = ''
        prev_level_name = ''
        for idx, name in enumerate(struct):
            # FIXME: replacing '_' is needed for current AREA names, will change in future verions
            if len(mapping.ix[mapping[name] == out_code.replace('_', ' ')]) > 0:
                level_name = name
                prev_level_name = struct[idx + 1]
                break
        stark_out = Stark(pandas.DataFrame(columns=COLUMNS), META)
        # Aggregate files
        fk = PRIMARYK[struct]
        for file_ in files:
            df = Stark.load(os.path.join(current, file_)).DF
            # FIXME: code is determined by the file name, this is not very reliable!
            code = os.path.basename(file_).replace('.pickle', '')
            df[level_name] = df[fk].map({code: out_code})
            # Drop old CODE and substitute with new one
            del df[fk]
            df = df.rename(columns={level_name: fk})
            stark_tmp = Stark(df, META)
            stark_out += stark_tmp
        full_path = os.path.join(current, os.path.pardir, out_file)
        _logger.debug('Saving %s', full_path)
        stark_out.save(full_path)

def init(input_dir, ulisse_codes, countries, uom):
    """ Init environment:
    - UL3000 mapping
    - country list
    - input file list
    """
    ul3000 = pandas.DataFrame.from_csv(ulisse_codes).reset_index()
    uom_df = pandas.DataFrame.from_csv(uom).reset_index()
    country_map = pandas.DataFrame.from_csv(countries).reset_index()
    file_list = [os.path.join(input_dir, file_)
                 for file_ in os.walk(input_dir).next()[2]]
    # TODO: extend META with country_map and UL info
    return (file_list, country_map, ul3000, uom_df)

def main(input_dir=None, root=None, start_year=None,
         countries=None, ulisse_codes=None, uom=None, 
         meta=None, product_tree=None, country_tree=None, 
         **kwargs):
    """
    Main procedure:
    """

    # pivot by contry
    file_list, country_map, ul3000, uom_df = init(input_dir, ulisse_codes, countries, uom)

    # Transform by UL codes and aggregate
    ul_root = os.path.join(root, 'prod/E3')
    from_hs('UL3000', input_dir, ul_root, ul3000)
    aggregate(ul_root, ul3000)
 
    # Transform by ISO3 code and aggregate
    iso3_root = os.path.join(root, 'country')
    by_country('UL1000', ul_root, iso3_root, country_map)
    aggregate(iso3_root, country_map, struct=STRUCT_COUNTRY)
   
    return 0


if __name__ == '__main__':
    config = Config(os.path.join(BASEPATH, 'config/ercole/ercole_sort.cfg'))
    config.parse()
    _logger = logging.getLogger(sys.argv[0])
    sys.exit(main(**config.options))
