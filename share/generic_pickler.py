# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
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
##############################################################################

try:
    import cPickle as pickle
except ImportError:
    import pickle

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'
__all__ = ['GenericPickler']

class GenericPickler(object):
    """ Simple common interface to hadle pickling and unpickling.
    Every class that need to be saved as a pickle should subclass this.
    """
    
    def save(self, file):
        """ Save objet as a pickle """
        pickle.dump(self, file)

    @staticmethod
    def load(file):
        """ Load object from a pickle """
        return pickle.load(file)
