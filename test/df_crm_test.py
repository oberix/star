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



'''
Created on 12/lug/2012

@author: lcirillo
'''

import sys
import pandas


sys.path.append('../star/trunk/')


import etl
import crm_mapping

dict_to_in = {
             'id' : ('id', None), 
             'create_date' : ('create_date', None), 
             'lead' : ('name', None),
             'contact' : ('contact_name', None),
             'partner' : ('partner', ('name', None)), 
             'date_action' : ('date_action', None),
             'title_action' : ('title_action', None),
             'stage' : ('stage', ('name', None)),
             'planned_revenue' : ('planned_revenue', None),
             'probability' : ('probability', None),
             'user' : ('user', ('name', None)),
             'state' : ('state', None),
             }

crm = crm_mapping.CrmLead

dict_out = etl.create_dict.create_dict(crm, dict_to_in)
df = pandas.DataFrame(dict_out)

gv_crm = {
      'id' : 
        {
         'NAME' : 'ID',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'id del record',
         'MUNIT' : '',
         'DATYP' : 'int',
         },
      'create_date' : 
        {
         'NAME' : 'CRT_DAT',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'id del record',
         'MUNIT' : '',
         'DATYP' : 'date',
         },
      'lead' : 
        {
         'NAME' : 'OPPRTNTY',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'descrizione opportunità',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'contact' : 
        {
         'NAME' : 'CNTCT',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'contatto del cliente',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'partner' : 
        {
         'NAME' : 'PRTNR',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'cliente',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'date_action' : 
        {
         'NAME' : 'ACT_DAT',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'data prossima azione',
         'MUNIT' : '',
         'DATYP' : 'date',
         },
      'title_action' : 
        {
         'NAME' : 'DES_ACT',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'descrizione prossima azione',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'stage' : 
        {
         'NAME' : 'STD',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'stadio dell\'opportunità',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'planned_revenue' : 
        {
         'NAME' : 'PREV_ENTR',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'entrata prevista',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'probability' : 
        {
         'NAME' : 'PRBLT',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'percentuale probabilità',
         'MUNIT' : '',
         'DATYP' : 'float',
         },
      'user' : 
        {
         'NAME' : 'VNDTR',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'commerciale',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      'state' : 
        {
         'NAME' : 'STATE',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'stato oppurtunità',
         'MUNIT' : '',
         'DATYP' : 'str',
         }
    }

strk_crm = etl.style.style(df, gv_crm)
