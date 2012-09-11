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
Created on 11/lug/2012
'''

import DBmap2
import sqlalchemy

def create_dict(cl_dmap2, dict_path, company_name):
    '''
    Create dictionary with database datas from:
    @param cl_dmap2: DBmap2 class
    @param dict_path: dictionary structured as:
                    { 'NAMEVAR' :
                        ('name attribute cl_dmap2', (...., None))
    return dictionary {
                        'NAMEVAR' : [data, data, data, .....]
                        }
    '''
    
    def tuple2attr(obj, tpl):
        el = tpl
        while(el[1] != None):
            obj = getattr(obj, el[0])
            el = el[1]
        if isinstance(obj,sqlalchemy.orm.collections.InstrumentedList):
            obj = obj[0]
        obj = getattr(obj, el[0])
        return obj
    
    def get_obj(session, cl_dbmap2, company_name):
        objs = None
        try:
            getattr(cl_dbmap2, 'company')
            objs = session.query(cl_dbmap2).filter(cl_dbmap2.company.has(name=company_name)).all()
        except AttributeError:    
            objs = session.query(cl_dbmap2).all()
        return objs
    
    session = DBmap2.open_session()
    out_dict = {}    
    objs = get_obj(session, cl_dmap2, company_name)
    for key in dict_path.iterkeys():
        out_dict[key] = []
    for obj in objs:
        for key in dict_path.iterkeys():
            try:
                out_dict[key].append(tuple2attr(obj, dict_path[key]))
            except AttributeError:
                out_dict[key].append(None)
    DBmap2.close_session(session)
    return out_dict