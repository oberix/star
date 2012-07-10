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
from share import stark


def style(df, gov):
    '''
    Create a StarK object of type elab from df and gov
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
    return: StarK object  
    '''
    
    def check_aggreg(aggreg, datyp, el):
        if aggreg == True:
            if datyp != 'str':
                raise TypeError("%s : 'AGGREG' is True but 'DATYP' not 'str'" %el)
        return True
            
    def set_des_rec(rec):
        rec_des = {}
        rec_des['AGGREG'] = rec['AGGREG']
        rec_des['DASTR'] = rec['DASTR']
        rec_des['DESVAR'] = rec['DESVAR']
        rec_des['MUNIT'] = rec['MUNIT']
        rec_des['DATYP'] = rec['DATYP']
        return rec_des
    
    def check_columns(df, col):
        df_col = df.columns.tolist()
        for item in col:
            iter_df = iter(df_col)
            item_df = iter_df.next()
            while (item != item_df):
                try:
                    item_df = iter_df.next()
                except StopIteration:
                    raise KeyError("Columns in gov not in df")
        return True
            
    
    ren = {}
    des = {}
    col = []    
    for el in gov.iterkeys():
        rec = gov[el]
        check_aggreg(rec['AGGREG'], rec['DATYP'], el)
        des[rec['NAME']] = set_des_rec(rec)
        ren[el] = rec['NAME']
        col.append(el)
    check_columns(df, col)
    df = pandas.DataFrame(df, columns = col)
    df = df.rename(columns = ren)
    goal2stark = stark.StarK(df, 'elab', COD = 'goal2stark', )
    goal2stark.DES = des
    return goal2stark
    
        
        
        
        
        
        
        
        
            