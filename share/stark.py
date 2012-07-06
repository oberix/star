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


import pandas
import sys
import cPickle



# Servabit libraries
#sys.path.append('../')


class StarK(object):
    '''
    StarK Class select and rename fields from Goal2df dataframe
    dataframe and hold a description about
    
    @GOV: public set dataframe structure, as {
            field name of final dataframe : 
                                     [
                                      field name goal2df dataframe,
                                      field decription,
                                      field unit measure,
                                      field type,
                                      set field to active with 'SI']
            }
            
    @des: private, dataframe decription structure, as {
            field name of final dataframe : 
                                     [
                                      field decription,
                                      field unit measure,
                                      field type]
            }
    
    @df: dataframe
    '''
    
    def __init__(self, DF, TYPE, COD = None, FOOTNOTE = None):
        '''
        Initialize:
        '''
        self.DF = DF
        self.TYPE = TYPE
        self.COD = COD
        self.FOOTNOTE = FOOTNOTE
        self.DES = {}
        self.TITLE = str
        self.__path = str
        if TYPE == 'elab':
            for e in self.DF.columns:
                self.DES[e] = {'AGGREG' : None, 'DASTR' : None, 'DESVAR' : None, 'MUNIT' : None, 'DATYP' : None, }
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
        Serialize DfMoveLine object
        
        @file_path_name: path/file_name.pickle
        '''
        f = open(self.__path + '/' + filename,'w')
        cPickle.dump(self)
        f.close()
    
    @staticmethod
    def Loadk(file_path, filename):
        '''
        Load  DfMoveLine object from pickle file
        
        @file_path_name: path/file_name.pickle
        '''
        f = open(file_path+ '/' + filename, 'r')
        starkobj = cPickle.load(f)
        f.close()
        return starkobj
        
