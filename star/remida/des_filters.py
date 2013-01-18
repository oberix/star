# -*- coding: utf-8 -*-

################################################################################
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
################################################################################

from operator import eq, lt, le, gt, ge
from operator import itemgetter as ig
from math import fabs

def length(data):
    try:
        return len(data)
    except:
        pass
    
    return unicode("", "utf8")

def approx(data, ndigits=0):
    try:
        if type(data) is list or type(data) is tuple:
            return [unicode("{0:.{1}f}", "utf8").format(float(e), int(ndigits)) 
                    for e in data]
        else:
            return unicode("{0:.{1}f}", "utf8").format(float(data), int(ndigits))
    except:
        pass
        
    return unicode("", "utf8")    

def absolute(data):
    try:
        if type(data) is list or type(data) is tuple:
            return [fabs(float(e)) for e in data]
        else:
            return fabs(float(data))
    except:
        pass
    
    return unicode("", "utf8")   

def first(data):
    try:
        res = data[0]
    except:
        res = unicode("", "utf8")
    return res

def last(data):
    try:
        res = data[-1]
    except:
        res = unicode("", "utf8")
    return res

def index(data, idx=0):
    try:
        return data[int(idx)]
    except:
        pass
    
    return unicode("", "utf8")

def pos(data, item):
    try:
        return data.index(item)
    except:
        pass
    
    return unicode("", "utf8")

def sort(data, reverse=False, item=None):
    try:
        if item:
            return sorted(data, reverse=reverse, key=ig(item))
        else:
            return sorted(data, reverse=reverse)
    except:
        pass

    return unicode("", "utf8")

def select(data, condition, item=None):
    if condition.startswith("eq_"):
        op = eq
    elif condition.startswith("gt_"):
        op = gt
    elif condition.startswith("lt_"):
        op = lt
    elif condition.startswith("ge_"):
        op = ge
    elif condition.startswith("le_"):
        op = le
    
    try:
        c = float(condition[3:])
        if item:
            if (item.startswith("\"") and item.endswith("\"") or
                item.startswith("'") and item.endswith("'")):
                return [e for e in data if op(float(e[item[1:-1]]), c)]
            else:
                return [e for e in data if op(float(e[int(item)]), c)]
        else:
            return [float(e) for e in data if op(float(e), c)]
    except:
        pass
    
    try:
        c = condition[3:]
        if item:
            if (item.startswith("\"") and item.endswith("\"") or
                item.startswith("'") and item.endswith("'")):
                return [e for e in data if op(e[item[1:-1]], c)]
            else:
                return [e for e in data if op(e[int(item)], c)]
        else:
            return [e for e in data if op(e, c)]                   
    except:
        pass
    
    return unicode("", "utf8")

def cut(data, start=0, end=None):
    try:
        start = int(start)
        if end:
            end = int(end)
        else:
            end = len(data)
        return data[start:end]
    except:
        pass
    
    return unicode("", "utf8")
    
def addtot(data, item=None):
    try:
        if item:
            if (item.startswith("\"") and item.endswith("\"") or
                item.startswith("'") and item.endswith("'")):
                return sum([float(e[item[1:-1]]) for e in data])
            else:
                return sum([float(e[int(item)]) for e in data])
        else:
            return sum([float(e) for e in data])
    except:
        pass

    return unicode("", "utf8")

def mean(data, item=None):
    try:
        if item:
            if (item.startswith("\"") and item.endswith("\"") or
                item.startswith("'") and item.endswith("'")):
                return sum([float(e[item[1:-1]]) for e in data]) / len(data)
            else:
                return sum([float(e[int(item)]) for e in data]) / len(data)
        else:
            return sum([float(e) for e in data]) / len(data)
    except:
        pass
    
    return unicode("", "utf8")

def multot(data, item=None):
    try:
        res = 1
        if item:
            if (item.startswith("\"") and item.endswith("\"") or
                item.startswith("'") and item.endswith("'")):
                for e in data:
                    res *= float(e[item[1:-1]])
            else:
                for e in data:
                    res *= float(e[int(item)])
        else:
            for e in data:
                res *= float(e)
        return res
    except:
        pass
    
    return unicode("", "utf8")

def add(data, other=0):
    try:
        return float(data) + float(other)
    except:
        pass
    
    return unicode("", "utf8")

def mul(data, other=1):
    try:
        return float(data) * float(other)
    except:
        pass
    
    return unicode("", "utf8")

def div(data, other=1):
    try:
        return float(data) / float(other)
    except:
        pass
    
    return unicode("", "utf8")

def sub(data, other=0):
    try:
        return float(data) - float(other)
    except:
        pass
    
    return unicode("", "utf8")

def power(data, other=0):
    try:
        return float(data) ** float(other)
    except:
        pass
    
    return unicode("", "utf8")

def get(data, key):
    try:
        return data.get(key, unicode("", "utf8"))
    except:
        pass
    
    return unicode("", "utf8")
