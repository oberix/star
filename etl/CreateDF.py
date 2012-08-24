#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
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

__VERSION__ = '0.1'
__AUTHOR__ = 'Luigi Cirillo (<luigi.cirillo@servabit.it>)'

import pandas
import sys
import os

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share import config
import DbMapping

def CreateDF(conf_path, def_dbmap, comp_name):
    '''
    Create dataframe from DbMapping functions
    @param conf_path: path of configuaration file
    @def_dbmap : point to function of DbMapping
    @param comp_name: company name
    
    return DataFrame 
    '''
    filename = os.path.join(conf_path, 'DbConfig.cfg')
    conf = config.Config(filename=filename)
    conf.parse()
    DbMapping.conf_goal = conf 
    data = def_dbmap(comp_name)
    df = pandas.DataFrame(data)
    return df
    
    
