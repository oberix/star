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
import pandas
import logging
try:
    import cPickle as pickle
except ImportError:
    import pickle

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

#import etl
from star.share import Config
from star.share import parallel_jobs
from star.share import Stark

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

# This are tuples because they are used as dict keys (and don't need to be
# changed anyway)
STRUCT_PROD = ('UL20', 'UL200', 'UL1000', 'UL3000')
STRUCT_COUNTRY = ('AREA', 'ISO3')
PRIMARYK = {STRUCT_PROD: 'CODE', STRUCT_COUNTRY: 'XER'}

_logger = logging.getLogger(sys.argv[0])

def _list_files(level, root):
    ''' Make a list of files at a given level of directory nesting, starting
    from root.

    @ param level: the nesting level to search as an integer
    @ param root: the directories tree root

    @ return: a list of paths
    '''
    out = []
    found = ([], [])
    for name in os.listdir(root):
        fullname = os.path.join(root, name)
        if os.path.isfile(fullname):
            found[1].append(fullname)
        elif os.path.isdir(fullname):
            found[0].append(fullname)
    dirs, files = found
    if level <= 0:
        # Target level reached
        out.extend(files)
    else:
        for dir_ in dirs:
            out.extend(_list_files(level-1, dir_))
    return out

def _by_country(root, mapping, country, group):
    '''Reshape DataFrames classified by product code into DataFrame organized
    by country (ISO3 code). A product aggregation level can be specified.

    This is the actual implementation, it's meant to be called by by_country()
    as separate process or iterativly.

    @ param root: output root path
    @ mapping: ISO3 code mapping DataFrame
    @ country: ISO3 code on which we are aggregating
    @ group: DataFrame containing records to be added

    '''
    stark_group = Stark(group, META)
    try:
        area = mapping.ix[country].replace(' ', '_')
    except KeyError:
        return
    out_file = os.path.join(root, area, '.'.join([country, 'pickle']))
    if not os.path.isfile(out_file):
        # create dir if it does not exists
        if not os.path.isdir(os.path.dirname(out_file)):
            os.makedirs(os.path.dirname(out_file))
        # Create a brand new Stark
        stark_group.save(out_file)
    else:
        fd = open(out_file, 'ab')
        try:
            pickle.dump(stark_group, fd, protocol=pickle.HIGHEST_PROTOCOL)
        finally:
            fd.close()

def _consolidate(file_):
    ''' Read Starks from a pickle and add them together, finally it saves back
    the result in the original file.

    @ param file_: path to the file to consolidate.
    '''
    _logger.info('Consolidating %s', file_)
    stark_out = Stark(pandas.DataFrame(columns=COLUMNS), META)
    fd = open(file_, 'r')
    while True:
        try:
            stark_curr = pickle.load(fd)
        except EOFError:
            # EOF reached
            break
        stark_out += stark_curr
    fd.close()
    stark_out.save(file_)

def _test_by_country(file_, root, mapping):
    ''' Utility function to debug _by_country() procedure.
    '''
    stark_curr = Stark.load(file_)
    groups = stark_curr.DF.groupby('XER')
    # Single process
    for country, group in groups:
        _by_country(root, mapping, country, group)

def by_country(level, in_path, root, mapping, key):
    ''' Reshape DataFrames classified by product code into DataFrame organized
    by country (ISO3 code). A product aggregation level can be specified.

    @ param level: product code aggregation level
    @ param in_path: input files root path
    @ param root: output root path
    @ mapping: ISO3 code mapping DataFrame
    @ key: variabla to group by

    '''
    # Make sure mapping is indicized by country
    mapping = mapping.reset_index().set_index('ISO3', drop=True)['AREA']
    files = _list_files(STRUCT_PROD.index(level), in_path)
    for idx, file_ in enumerate(files):
        _logger.info('Inspecting file %s: %s', idx, file_)
        if _logger.getEffectiveLevel() <= logging.DEBUG:
            # DEBUG: execute in a single process and take timig
            import timeit
            t = timeit.Timer(lambda: _test_by_country(file_, root, mapping), 'gc.enable()')
            _logger.debug('Time: %s sec', t.timeit(number=1))
        else:
            # Run multiprocess
            stark_curr = Stark.load(file_)
            groups = stark_curr.DF.groupby(key)
            args = [(_by_country, [root, mapping, country, group])
                    for country, group in groups]
            parallel_jobs.do_jobs_efficiently(args)
    # Consolidate pickles
    files = _list_files(STRUCT_COUNTRY.index('ISO3'), root)
    if _logger.getEffectiveLevel() <= logging.DEBUG:
        for file_ in files:
            t = timeit.Timer(lambda: _consolidate(file_), 'gc.enable()')
            _logger.debug('Time: %s sec', t.timeit(number=1))
    else:
        # Run multiprocess
        args = [(_consolidate, [file_]) for file_ in files]
        parallel_jobs.do_jobs_efficiently(args)

def _from_hs(level, in_path, root, code, group, start_year):
    ''' Aggregate form HS6digit into Ulisse classification.

    @ param level: aggregation level
    @ param in_path: list of input files
    @ param root: root directory for output
    @ param code: target product code
    @ param group: other code converging into code.

    '''
    _logger.info('Converting to %s', code)
    stark_out = Stark(pandas.DataFrame(columns=COLUMNS), META)
    # Make the aggregation
    for hs in group['HS07']:
        in_file = os.path.join(in_path, '.'.join([hs, 'pickle']))
        try:
            df = pandas.load(in_file)
        except IOError:
            # File does not exists
            continue
        df = df.ix[df['YEAR'] >= start_year]
        df['CODE'] = len(df) * [code]
        df.consolidate(inplace=True) # Should reduce memory usage
        stark_tmp = Stark(df, META)
        stark_out += stark_tmp
    # Build the out path by fetching the current code's record and
    # concatenating it's ancestors.
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

def from_hs(level, in_path, root, prod_map, start_year):
    ''' Convert DataFrames from HS6digit classification to Ulisse
    classification.

    This is just a wrapper to run the conversion with multiple processes. See
    _from_hs() for the aggregation algorithm.

    @ param level: aggregation level
    @ param in_path: list of input files
    @ param root: root directory for output
    @ param prod_map: product codes mapping DataFrame
    @ param start_year: record must have YEAR >= start_year

    '''
    prod_groups = prod_map.groupby(level)
    if _logger.getEffectiveLevel() <= logging.DEBUG:
        for code, group in prod_groups:
            _from_hs(level, in_path, root, code, group, start_year)
    else:
        args = [(_from_hs, [level, in_path, root, code, group, start_year]) for code, group in prod_groups]
        parallel_jobs.do_jobs_efficiently(args)

def aggregate(root, mapping, pkey=None):
    ''' Aggregates DataFrames stored in Python pickle files. This function
    performs a bottom-up walk of a directory subtree, aggregating DataFrames in
    each directory and storing the resulting DataFrame in the parent folder.

    @ param root: output root dir
    @ param mapping: product codes mapping DataFrame
    '''
    walker = os.walk(root, topdown=False)
    if pkey is None:
        pkey = 'CODE'
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
        # FIXME: Relay on file names to find codes is not very safe.
        if current == root:
            # root reached: evaluate total
            out_code = 'TOT'
            out_file = '_'.join([os.path.basename(root.rstrip(os.path.sep)), 'TOT.pickle'])
        else:
            out_code = os.path.split(current)[1]
            out_file = '.'.join([out_code, 'pickle'])
        # Aggregate files
        _logger.info('Aggregating by %s', out_code)
        stark_out = Stark(pandas.DataFrame(columns=COLUMNS), META)
        for file_ in files:
            # Find in_code
            stark_in = Stark.load(os.path.join(current, file_))
            try:
                in_code = stark_in.DF[pkey].unique()[0]
            except IndexError:
                # Empty DataFrame
                continue
            # Substitute in_code with out_code in source DF
            stark_in.DF[pkey] = stark_in.DF[pkey].map({in_code: out_code})
            stark_out += stark_in
            stark_in.DF.consolidate(inplace=True) # Saves a lot of memory here!
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
    # TODO: extend META with country_map and UL info
    return (country_map, ul3000, uom_df)

def main(input_dir=None, root=None, start_year=None,
         countries=None, ulisse_codes=None, uom=None,
         country_aggr_level='UL20', prod_aggr_level='UL3000',
         **kwargs):
    """
    Main procedure:
    """

    # pivot by contry
    country_map, ul3000, uom_df = init(input_dir, ulisse_codes, countries, uom)

    # Transform by UL codes and aggregate
    ul_root = os.path.join(root, 'prod')
    from_hs(prod_aggr_level, input_dir, ul_root, ul3000, start_year)
    aggregate(ul_root, ul3000)

    # # Transform by ISO3 code and aggregate
    iso3_root = os.path.join(root, 'country_MER')
    by_country(country_aggr_level, ul_root, iso3_root, country_map, 'MER')
    aggregate(iso3_root, country_map, pkey='MER')

    # # FIXME: this is redundant
    iso3_root = os.path.join(root, 'country_XER')
    by_country(country_aggr_level, ul_root, iso3_root, country_map, 'XER')
    aggregate(iso3_root, country_map, pkey='XER')

    return 0


if __name__ == '__main__':
    config = Config(os.path.join(BASEPATH, 'config/ercole/ercole_sort.cfg'))
    config.parse()
    _logger = logging.getLogger(sys.argv[0])
    sys.exit(main(**config.options))
