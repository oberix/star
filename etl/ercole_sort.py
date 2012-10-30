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
    'UL1000',
    'XER',
    # 'AREAX',
    'MER', 
    # 'AREAM', 
    'X', 
    'M', 
    'K', 
    'U',
    'Q']

# TODO: evaluate from meta
STRUCT_PROD = ['product', 'ul20', 'ul200', 'ul1000', 'ul3000']
STRUCT_COUNTRY = ['geo', 'area', 'country', 'region', 'province']

_logger = logging.getLogger(sys.argv[0])


def by_country(files, country, out_path, prod_mapping, start_year=None):
    """ Generate a dataframe with trade flow of a signle country, reading data
    from dataframes containing trade flow by product.
    """
    _logger.info('Extracting %s', ' '.join(country))
    out_df = pandas.DataFrame(columns=COLUMNS)
    for file_ in files:
        try:
            df = pandas.load(file_).groupby(
                ['XER']).get_group(country).reset_index()
        except KeyError: # contry not found in this file_
            continue
        if start_year is not None:
            df = df.ix[df['YEAR'] >= start_year]
        df['HS07'] = len(df) * [os.path.basename(file_.split('.')[0])]
        df.consolidate(inplace=True) # should reduce memory usage
        df = df.merge(prod_mapping, on='HS07')
        out_df = out_df.append(df)
    filename = '.'.join([os.path.join(out_path, *[name.replace(' ', '_') for name in country]), 'pickle'])
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    out_df.groupby(['UL1000', 'YEAR', 'R', 'MER']).\
        sum().reset_index()[COLUMNS].save(filename)

def build_tree(src, root, struct):
    """ Create output directory structure as defined with a metadata
    dictionary.
    """
    full_path = os.path.join(root, *struct)
    files = os.walk(src).next()[2]
    for file_ in files:
        os.renames(os.path.join(src, file_), os.path.join(full_path, file_))

# def aggregate(filename):
#     """ Aggregation magic
#     - 
#     """
#     # FIXME: This is just a draft implementaton
#     dirname = os.path.dirname(filename)
#     outdir = os.path.join(os.path.pardir, dirname)
# #    outname = #????
#     meta = eval(open(os.path.join(dirname, '__meta__.py'), 'r').read())
#     df = pandas.load(filename)
#     stark = Stark(df, meta)
#     aggregated = stark.aggregate()
#  #   stark.save(os.path.join(outdir, outname)

def init(input_dir, ulisse_codes, countries):
    """ Init environment:
    - UL3000 mapping
    - country list
    - input file list
    """
    ul3000 = pandas.DataFrame.from_csv(ulisse_codes).reset_index()
    reader = csv.reader(open(countries, 'r'))
    reader.next() # skip header
    country_list = [tuple(row) for row in reader]
    file_list = [os.path.join(input_dir, file_)
                 for file_ in os.walk(input_dir).next()[2]]
    return (file_list,  country_list, ul3000)

def main(input_dir=None, root=None, start_year=None,
         countries=None, ulisse_codes=None, meta=None,
         product_tree=None, country_tree=None, 
         **kwargs):
    """
    Main procedure:
    """

    # if _logger.getEffectiveLevel() == logging.DEBUG:
    #     import ipdb; ipdb.set_trace()

    # TODO: handle default Nones

    # pivot by contry
    file_list, country_list, ul3000 = init(input_dir, ulisse_codes, countries)

    if _logger.getEffectiveLevel() == logging.DEBUG:
        by_country(file_list, country_list[0], root, ul3000, start_year)
    else:
        args = [(by_country, [file_list, country, root, ul3000, start_year])
                for country in country_list]
        parallel_jobs.do_jobs_efficiently(args)

    # # aggregate countries by prod
    # build_tree(root, root, STRUCT_PROD)

    # # aggregate prod by cuuntry
    # build_tree(input_dir, root, STRUCT_COUNTRY)

    return 0


if __name__ == '__main__':
    
    config = Config(os.path.join(BASEPATH, 'config/ercole/ercole_sort.cfg'))
    config.parse()
    _logger = logging.getLogger(sys.argv[0])

    sys.exit(main(**config.options))
