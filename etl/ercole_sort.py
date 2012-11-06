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

#import etl
from share import Config
from share import parallel_jobs
#from share import Stark

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
STRUCT_COUNTRY = ['geo', 'area', 'country', 'region', 'province']
AGGR_LVL = 'UL1000'

_logger = logging.getLogger(sys.argv[0])


def by_country(files, country, out_path, prod_mapping, ums=None, start_year=None):
    """ Generate a dataframe with trade flow of a signle country, reading data
    from dataframes containing trade flow by product.
    """
    _logger.info('Extracting %s', ' '.join(country))
    out_df = pandas.DataFrame(columns=COLUMNS)
    for file_ in files:
        try:
            df = pandas.load(file_).groupby(
                ['AREAX', 'XER']).get_group(country).reset_index()
        except KeyError: # contry not found in this file_
            continue
        if start_year is not None:
            df = df.ix[df['YEAR'] >= start_year]
        # Add prod code
        df['HS07'] = len(df) * [os.path.basename(file_.split('.')[0])]
        df.consolidate(inplace=True) # should reduce memory usage
        df = df.merge(prod_mapping, on='HS07')
        # FIXME: Consider Unit of Measure
#        df = df.merge(ums, on='HS07')
        out_df = out_df.append(df, ignore_index=True)
    filename = '.'.join([os.path.join(out_path, *[name.replace(' ', '_') for name in country]), 'pickle'])
    # Create dir if it does not already exist
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    out_df.groupby(['UL1000', 'YEAR', 'R', 'XER', 'MER']).sum().reset_index()[COLUMNS].save(filename)

def from_hs(level, in_path, root, prod_map, uom):
    '''
    @ param level: aggregation level
    @ param in_path: list of input files
    @ param root: root directory for output
    @ param prod_map: product codes mapping DataFrame
    @ param uom: product units of measure DataFrame
    ''' 
    # TODO: use Starks!
    df_out = pandas.DataFrame(columns=COLUMNS)
    prod_groups = prod_map.groupby(level)
    for code, group in prod_groups:
        for hs in group['HS07']:
            try:
                df = pandas.load(os.path.join(in_path, '.'.join([hs, 'pickle'])))
            except IOError:
                # File does not exists
                continue
            df['CODE'] = len(df) * [code]
            df.consolidate(inplace=True) # Should reduce memory usage
            # TODO: Handle non summable quantities
            df_out = df_out.append(df[COLUMNS], verify_integrity=False).groupby(DIMENSIONS).sum().reset_index()
        path = group.set_index('HS07')[STRUCT_PROD[:STRUCT_PROD.index(level)]].ix[0].tolist()
        path.insert(0, root)
        path.append(code)
        filename = '.'.join([os.path.join(*path), 'pickle'])
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        df_out.save(filename)
        
# def aggregate(root, mapping):
#     '''
#     @ param root: output root dir
#     @ param mapping: product codes mapping DataFrame
#     '''
#     walker = os.walk(root, topdown=False)
#     for current, dirs, files in walker:
#         df_out = pandas.DataFrame(columns=COLUMNS)
#         for file_ in files:
#             df_out = df_out.append(pandas.load(file_))
#         # level = current.split(file_)[0].replace('.pickle', '')
#         level_idx = STRUCT_PROD.index(os.path.split(current)[1])
# #        df_out.merge(

            

def init(input_dir, ulisse_codes, countries, ums):
    """ Init environment:
    - UL3000 mapping
    - country list
    - input file list
    """
    ul3000 = pandas.DataFrame.from_csv(ulisse_codes).reset_index()
    ums_df = pandas.DataFrame.from_csv(ums).reset_index()
    reader = csv.reader(open(countries, 'r'))
    reader.next() # skip header
    country_list = [tuple(row) for row in reader]
    file_list = [os.path.join(input_dir, file_)
                 for file_ in os.walk(input_dir).next()[2]]
    return (file_list, country_list, ul3000, ums_df)

def main(input_dir=None, root=None, start_year=None,
         countries=None, ulisse_codes=None, ums=None, 
         meta=None, product_tree=None, country_tree=None, 
         **kwargs):
    """
    Main procedure:
    """

    # if _logger.getEffectiveLevel() == logging.DEBUG:
    #     import ipdb; ipdb.set_trace()

    # TODO: handle default Nones

    # pivot by contry
    file_list, country_list, ul3000, ums_df = init(input_dir, ulisse_codes, countries, ums)

    from_hs('UL3000', input_dir, root, ul3000, ums)
    
    # if _logger.getEffectiveLevel() == logging.DEBUG:
    #     for country in country_list[40:]:
    #         by_country(file_list, country, root, ul3000, ums_df, start_year)
    # else:
    #     args = [(by_country, [file_list, country, root, ul3000, ums_df, start_year])
    #             for country in country_list]
    #     parallel_jobs.do_jobs_efficiently(args)

    return 0


if __name__ == '__main__':
    
    config = Config(os.path.join(BASEPATH, 'config/ercole/ercole_sort.cfg'))
    config.parse()
    _logger = logging.getLogger(sys.argv[0])
    sys.exit(main(**config.options))
