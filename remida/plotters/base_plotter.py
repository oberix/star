# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
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

import logging

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"


class BasePlotter(object):
    ''' Generic class defining the interface of a Plotter.

    A Plotter is an abject capable of drawing a graph in an axis system inside
    a figure's subplot. 

    The Plotter is just a strategy class, a Graph instance must pass itself
    when initializing a Plotter to let it have easy acccess to any graph
    attribute.

    Each BasePlotter subclass have to implement the plot() method with a
    specific drowing algorithm.

    BasePlotter has the following attributes:

    @ attib self._graph: a Graph instance
    @ attrib self._logger: a Logger
    '''
    
    def __init__(self, graph):
        self._graph = graph
        self._logger = logging.getLogger(type(self).__name__)

    def plot(self, ax, column, **kwargs):
        ''' Abstarct method defining the interface for the plotting function.
        
        @ param ax: an AxisSubplot object as returned from Figure.add_subplot()
        @ param column: a dict containing column metadata (data can be accessed
            through self._graph
        @ return: list of matplotlib object that constitute the plot.
        '''
        raise NotImplementedError


        
