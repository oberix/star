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

import sys
import pandas

# Servabit libraries
sys.path.append('../')
from share import Stark


def style(df, gov):
    '''
    Create a Stark object of type elab from df and gov
    @param df: DataFrame
    @param gov: dict as {
        field name of initial dataframe:
            {
             'NAME' : field name of final dataframe,
             'AGGREG' : Boolean indicating the aggregation
             'DASTR' : dictionary with other informations about column,
             'DESVAR' : description,
             'MUNIT' : unit measure,
             'DATYP' : column type,
             }
           }
    return: Stark object  
    '''
    
    def check_vartype(vartype, datyp, el):
        if vartype == True:
            if datyp != 'str':
                raise TypeError("%s : 'VARTYPE' is True but 'DATYP' not 'str'" %el)
        return True
            
    def set_des_rec(rec):
        rec_des = {}
        rec_des['VARTYPE'] = rec['VARTYPE']
        rec_des['DASTR'] = rec['DASTR']
        rec_des['DESVAR'] = rec['DESVAR']
        rec_des['MUNIT'] = rec['MUNIT']
        rec_des['DATYP'] = rec['DATYP']
        return rec_des
    
    def check_columns(df, col):
        '''
        confronto df e col
        '''
        df_col = df.columns.tolist()
        for item in col:
            try:
                df_col.index(item)
            except ValueError:
                raise ValueError("Columns in gov not in df")
        return True
            
    
    ren = {}
    des = {}
    col = []    
    for el in gov.iterkeys():
        rec = gov[el]
        #import ipdb; ipdb.set_trace()
        check_vartype(rec['VARTYPE'], rec['DATYP'], el)
        des[rec['NAME']] = set_des_rec(rec)
        ren[el] = rec['NAME']
        col.append(el)
    check_columns(df, col)
    df = pandas.DataFrame(df, columns = col)
    df = df.rename(columns = ren)
    goal2stark = Stark(df, 'elab' )
    goal2stark.DES = des
    return goal2stark
