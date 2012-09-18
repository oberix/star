# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Luigi Cirillo (<luigi.cirillo@servabit.it>)
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
'''
    Stark Class select and rename fields from Goal2df Move Line
    dataframe and hold a description about
.'''
__version__ = '0.1'
__author__ = 'Luigi Cirillo (<luigi.cirillo@servabit.it>)'
__all__ = ['Stark']

import sys
import os 

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share import GenericPickler

TI_VALS = (
    'elab'
)

class Stark(GenericPickler):
    ''' This is the artifact that outputs mainly from etl procedures. It is a
    collection of meta-information around datas inside a pandas DataFrame.

    Stark has the following attributes:
        DF: a pandas DataFrame
        LD: the path where the object will be saved as pickle
        TI: type (just 'elab' for now)
        VD: a a dictionary of various info for the user; keys are DF columns
        names, each key contain a dictionary with the following keys.
            TIP: data use, one of (D|N|S|R), that stands for:
                Dimension: can be used in aggregation (like groupby)
                Numeric: a numeric data type
                String: a string data type
                Calculated: (Ricavato in Italian)
            DES: a short description
            MIS: unit of measure
            ELA: elaboration that ptocuced the data (if TIP == 'R')

    '''

    def __init__(self, DF, LD, TI='elab', VD=None):
        self.DF = DF
        self.LD = LD
        if TI not in TI_VALS:
            raise ValueError("TI must be one of %s" % TI_VALS)
        self.TI = TI
        if VD is None:
            VD = {}
        if not set(VD.keys()).issubset(set(DF.columns.tolist())):
            raise ValueError("VD.keys() must be a subset of DF.columns")
        self.VD = VD

    def save(self, file_=None):
        if file_ is None:
            file_ = self.LD
        if not os.path.exists(os.path.dirname(file_)):
            os.makedirs(os.path.dirname(file_))
        super(Stark, self).save(file_)

