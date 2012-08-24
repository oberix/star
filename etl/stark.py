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
    StarK Class select and rename fields from Goal2df Move Line
    dataframe and hold a description about
.'''
__VERSION__ = '0.1'
__AUTHOR__ = 'Luigi Cirillo (<luigi.cirillo@servabit.it>)'

import sys
import os

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share.generic_pickler import GenericPickler

class StarK(GenericPickler):
    '''
    StarK Class 
    '''
    
    def __init__(self, DF, TYPE, COD = None, TITLE = None, FOOTNOTE = None):
        '''
        Initialize:
        '''
        self.DF = DF
        self.TYPE = TYPE
        self.COD = COD
        self.FOOTNOTE = FOOTNOTE
        self.DES = {}
        self.TITLE = str()
        self.__path = str() # FIXME: what's this for?
        if TYPE == 'elab':
            for e in self.DF.columns:
                self.DES[e] = {'VARTYPE' : None, 'DASTR' : None, 'DESVAR' : None, 'MUNIT' : None, 'DATYP' : None, }
        if TYPE == 'tab':
            for e in self.DF.columns:
                self.DES[e] = {'ORD' : None, 'H1' : None, 'H2' : None, 'H3' : None, 'POS' : None, }
        if TYPE == 'graph':
            for e in self.DF.columns:
                self.DES[e] = {'WUSE' : None, 'AXES' : None, 'LEG' : None}
  
    def DefPathPkl(self, path):
        self.__path = path
    
    def Dumpk(self, filename):
        '''
        Serialize Stark object
        
        Parameters
        ----------
        filename: string, file_name.pickle
        '''
        #import ipdb; ipdb.set_trace()
        print(self.__path)
        f = open(self.__path + '/' + filename,'wb')
        try:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
        finally:
            f.close()
    
    @staticmethod
    def Loadk(file_path, filename):
        """
        Load Stark object from pickle file from the specified
        file path
    
        Parameters
        ----------
        file_path : string, file path
        filename : string, file name
    
        Returns
        -------
        unpickled : type of Stark object stored in file
        """
        f = open(file_path+ '/' + filename, 'rb')
        try:
            starkobj = pickle.load(f)
            return starkobj
        finally:
            f.close()
