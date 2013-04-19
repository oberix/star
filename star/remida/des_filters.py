# -*- coding: utf-8 -*-

###############################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Luigi Curzi <tremst@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 2 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from operator import eq, lt, le, gt, ge
from operator import itemgetter as ig
import logging
import traceback as trb
import decimal as dc

# FIXME: migliore gestione di utf8

def length(data):
    logging.debug(u"filtro 'length': data='{0}'".format(data))    
    res = unicode("", "utf8")
    try:
        res = len(data)
    except:
        logging.warning(u"filtro 'length': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'length': risultato='{0}'".format(res))
    return res 


def approx(data, ndigits=0):
    logging.debug(u"filtro 'approx': data='{0}', ndigits='{1}'"
                  "".format(data, ndigits))
    res = unicode("", "utf8")
    try:
        if isinstance(data,(list, tuple)):
            # approssimiamo ogni elemento della lista
            res = [dc.Decimal(unicode("{0:.{1}f}", "utf8")\
                          .format(dc.Decimal(str(e)), int(ndigits))) 
                   for e in data]
        else:
            res = dc.Decimal(unicode("{0:.{1}f}", "utf8")\
                                .format(dc.Decimal(str(data)), int(ndigits)))
    except:
        logging.warning(u"filtro 'approx': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'approx': risultato='{0}'".format(res))
    return res    


def absolute(data):
    logging.debug(u"filtro 'absolute': data='{0}'".format(data))
    res = unicode("", "utf8")
    try:
        if isinstance(data, (list, tuple)):
            # calcoliamo il valore assoluto di ogni elemento della lista
            res = [dc.Decimal(str(e)).copy_abs() for e in data]
        else:
            res = dc.Decimal(str(data)).copy_abs()
    except:
        logging.warning(u"filtro 'absolute': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'absolute': risultato='{0}'".format(res))
    return res   


def first(data):
    logging.debug(u"filtro 'first': data='{0}'".format(data))
    res = unicode("", "utf8")
    try:
        res = data[0]
    except:
        logging.warning(u"filtro 'first': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'first': risultato='{0}'".format(res))
    return res


def last(data):
    logging.debug(u"filtro 'last': data='{0}'".format(data))
    res = unicode("", "utf8")
    try:
        res = data[-1]
    except:
        logging.warning(u"filtro 'last': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'last': risultato='{0}'".format(res))
    return res


def index(data, idx=0):
    logging.debug(u"filtro 'index': data='{0}', idx='{1}'".format(data, idx))
    res = unicode("", "utf8")
    try:
        res = data[int(idx)]
    except:
        logging.warning(u"filtro 'index': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'index': risultato='{0}'".format(res))
    return res


def pos(data, item):
    logging.debug(u"filtro 'pos': data='{0}', item='{1}'".format(data, item))
    res = unicode("", "utf8")
    try:
        res = data.index(item)
    except:
        logging.warning(u"filtro 'pos': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'pos': risultato='{0}'".format(res))
    return res


def sort(data, reverse=False, item=None):
    logging.debug(u"filtro 'sort': data='{0}', reverse='{1}', item='{2}'"
                  "".format(data, reverse, item))
    res = unicode("", "utf8")
    try:
        if item: 
            if isinstance(item, dc.Decimal):
                item = int(item)           
            res = sorted(data, reverse=reverse, key=ig(item))
            logging.debug(u"filtro 'sort': risultato='{0}'".format(res))
            return res
        else:
            res = sorted(data, reverse=reverse)
    except:
        logging.warning(u"filtro 'sort': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'sort': risultato='{0}'".format(res))
    return res


def select(data, condition, value, item=None):
    logging.debug(u"filtro 'select': data='{0}', condition='{1}', item='{2}'"
                  "".format(data, condition, item))
    res = unicode("", "utf8")
    if condition == "eq":
        op = eq
    elif condition == "gt":
        op = gt
    elif condition == "lt":
        op = lt
    elif condition == "ge":
        op = ge
    elif condition == "le":
        op = le
    try:
        if isinstance(value, dc.Decimal):
            if item:
                if isinstance(item, dc.Decimal):
                    item = int(item)
                res = [e for e in data if op(dc.Decimal(str(e[item])), value)]
            else:
                res = [dc.Decimal(str(e)) for e in data if 
                       op(dc.Decimal(str(e)), value)]
        else:
            if item:
                if isinstance(item, dc.Decimal):
                    item = int(item)
                res = [e for e in data if op(e[item], value)]        
            else:
                res = [e for e in data if op(e, value)]
    except:
        logging.warning(u"filtro 'select': {0}".format(trb.format_exc()))        
    logging.debug(u"filtro 'select': risultato='{0}'".format(res))
    return res


def cut(data, start=0, end=None):
    logging.debug(u"filtro 'cut': data='{0}', start='{1}', end='{2}'"
                  "".format(data, start, end))
    res = unicode("", "utf8")
    try:
        start = int(start)
        if end:
            end = int(end)
        else:
            end = len(data)
        res = data[start: end]
    except:
        logging.warning(u"filtro 'cut': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'cut': risultato='{0}'".format(res))
    return res


def addtot(data, item=None):
    return sumtot(data, item)


def sumtot(data, item=None):
    logging.debug(u"filtro 'sumtot': data='{0}', item='{1}'".format(data, 
                                                                    item))
    res = unicode("", "utf8")
    try:
        if item:
            if isinstance(item, dc.Decimal):
                item = int(item)
            res = sum([dc.Decimal(str(e[item])) for e in data])
        else:
            res = sum([dc.Decimal(str(e)) for e in data])
    except:
        logging.warning(u"filtro 'sumtot': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'sumtot': risultato='{0}'".format(res))
    return res


def mean(data, item=None):
    logging.debug(u"filtro 'mean': data='{0}', item='{1}'".format(data, item))
    res = unicode("", "utf8")
    try:
        if item:
            if isinstance(item, dc.Decimal):
                item = int(item)
            res = sum([dc.Decimal(str(e[item])) for e in data]) / len(data)
        else:
            res = sum([dc.Decimal(str(e)) for e in data]) / len(data)
    except:
        logging.warning(u"filtro 'mean': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'mean': risultato='{0}'".format(res))
    return res


def multot(data, item=None):
    return prodtot(data, item)
    
    
def prodtot(data, item=None):
    logging.debug(u"filtro 'prodtot': data='{0}', item='{1}'".format(data, 
                                                                     item))
    res = unicode("", "utf8")
    try:
        res = 1
        if item:
            if isinstance(item, dc.Decimal):
                item = int(item)
            for e in data:
                res *= dc.Decimal(str(e[item]))
        else:
            for e in data:
                res *= dc.Decimal(str(e))
    except:
        logging.warning(u"filtro 'prodtot': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'prodtot': risultato='{0}'".format(res))
    return res


def add(data, other=0):
    logging.debug(u"filtro 'add': data='{0}', other='{1}'".format(data, other))
    res = unicode("", "utf8")
    try:
        res = dc.Decimal(str(data)) + other
    except:
        logging.warning(u"filtro 'add': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'add': risultato='{0}'".format(res))
    return res


def mul(data, other=1):
    return prod(data, other)


def prod(data, other=1):
    logging.debug(u"filtro 'prod': data='{0}', other='{1}'".format(data, 
                                                                   other))
    res = unicode("", "utf8")
    try:
        res = dc.Decimal(str(data)) * other
    except:
        logging.warning(u"filtro 'prod': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'prod': risultato='{0}'".format(res))
    return res


def div(data, other=1):
    logging.debug(u"filtro 'div': data='{0}', other='{1}'".format(data, other))
    res = unicode("", "utf8")
    try:
        res = dc.Decimal(str(data)) / other
    except:
        logging.warning(u"filtro 'div': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'div': risultato='{0}'".format(res))
    return res


def sub(data, other=0):
    logging.debug(u"filtro 'sub': data='{0}', other='{1}'".format(data, other))
    res = unicode("", "utf8")
    try:
        res = dc.Decimal(str(data)) - other
    except:
        logging.warning(u"filtro 'sub': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'sub': risultato='{0}'".format(res))
    return res


def power(data, other=0):
    logging.debug(u"filtro 'power': data='{0}', other='{1}'".format(data, 
                                                                    other))
    res = unicode("", "utf8")
    try:
        res = dc.Decimal(str(data)) ** other
    except:
        logging.warning(u"filtro 'power': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'power': risultato='{0}'".format(res))
    return res


def get(data, key):
    logging.debug(u"filtro 'get': data='{0}', key='{1}'".format(data, key))
    res =  unicode("", "utf8")
    try:
        if isinstance(data, dict):
            res = data[key]
        else:
            res = [i[key] for i in data]
    except:
        logging.warning(u"filtro 'get': {0}".format(trb.format_exc()))
    logging.debug(u"filtro 'get': risultato='{0}'".format(res))
    return res
