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
from share import Stark


BASE_IN = '/home/mpattaro/workspace/sql/ercole/'
BASE_OUT = '/tmp/ercole2'
COUNTRY_LIST = '/home/mpattaro/workspace/star/trunk/etl/PaesiUlisse.csv'
UL3000 = '/home/mpattaro/workspace/star/trunk/etl/UL3000.csv'
START_YEAR = '1995'
COLUMNS = [
    'R', 
    'YEAR', 
    'UL3000',
    # 'XER',
    # 'AREAX',
    'MER', 
    'AREAM', 
    'X', 
    'M', 
    'K', 
    'U',
    'Q']

STRUCT_PROD = ['product', 'ul20', 'ul200', 'ul1000', 'ul3000']
STRUCT_COUNTRY = ['geo', 'area', 'country', 'region', 'province']

META_PROD = {
    'AREAX': {
        'TYPE': 'D',
        'ORD': 0,
        'child': {
            'XER': {
                'TYPE': 'D'}}},
    'AREAM': {
        'TYPE': 'D',
        'ORD': 1,
        'child': {
            'MER': {
                'TYPE': 'D'}}},
    'YEAR': {
        'TYPE': 'D',
        'ORD': 2},
    'R': {
        'TYPE': 'D',
        'ORD': 3},
    'X': {'TYPE': 'N'},
    'M': {'TYPE': 'N'},
    'K': {'TYPE': 'N'},
    'U': {'TYPE': 'N'},
    'Q': {'TYPE': 'N'}
    }

META_COUNTRY = {
    'UL20': {
        'TYPE': 'D',
        'ORD': 0,
        'child': {
            'UL200': {
                'TYPE': 'D',
                'child': {
                    'UL1000': {
                        'TYPE': 'D',
                        'child': {
                            'UL3000':{
                                'TYPE': 'D'}
                            }
                        }
                    }
                }
            }
        },
    'AREAM': {
        'TYPE': 'D',
        'ORD': 1,
        'child': {
            'MER': {
                'TYPE': 'D'}}},
    'YEAR': {
        'TYPE': 'D',
        'ORD': 2},
    'R': {
        'TYPE': 'D',
        'ORD': 3},
    'X': {'TYPE': 'N'},
    'M': {'TYPE': 'N'},
    'K': {'TYPE': 'N'},
    'U': {'TYPE': 'N'},
    'Q': {'TYPE': 'N'}
    }

_logger = logging.getLogger(sys.argv[0])


def by_country(files, country, out_path, prod_mapping, start_year='1995'):
    """ Generate a dataframe with trade flow of a signle country, reading data
    from dataframes containing trade flow by product.
    """
    _logger.info('Extracting %s', ' '.join(country))
    if not os.path.isdir(out_path):
        os.makedirs(out_path)
    out_df = pandas.DataFrame(columns=COLUMNS)
    for file_ in files:
        try:
            df = pandas.load(file_).groupby(
                ['AREAX', 'XER']).get_group(country).reset_index()
        except KeyError: # contry not found in this file_
            continue
        df = df.ix[df['YEAR'] >= start_year]
        df['HS07'] = len(df) * [os.path.basename(file_.split('.')[0])]
        df.consolidate(inplace=True) # should reduce memory usage
        df = df.merge(prod_mapping, on='HS07')
        out_df = out_df.append(df)
    out_df.groupby(['UL3000', 'YEAR', 'R', 'AREAM', 'MER']).\
        sum().reset_index()[COLUMNS].save(
        '.'.join([os.path.join(out_path, '_'.join(country).replace(' ', '_')), 
                  'pickle']))

def build_tree(src, root, struct):
    """ Create output directory structure as defined with a metadata
    dictionary.
    """
    full_path = os.path.join(root, *struct)
    files = os.walk(src).next()[2]
    for file_ in files:
        os.renames(os.path.join(src, file_), os.path.join(full_path, file_))


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

def aggregate(filename):
    dirname = os.path.dirname(filename)
    outdir = os.path.join(os.path.pardir, dirname)
#    outname = #????
    meta = eval(open(os.path.join(dirname, '__meta__.py'), 'r').read())
    df = pandas.load(filename)
    stark = Stark(df, meta)
    aggregated = stark.aggregate()
 #   stark.save(os.path.join(outdir, outname)


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
        by_country(file_list, country_list[0], root, ul3000)
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
