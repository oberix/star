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

import plotters
import logging

class BasePlotter(object):
    
    def __init__(self, graph):
        self._graph = graph

    def plot(self, ax, **kwargs):
        raise NotImplementedError

class Plotters(object):
    ''' Plotter factory.
    Just to ensure every plotter has one and only one instance.
    '''

    def __init__(self, graph):
        self._graph = graph
        self._logger = logging.getLogger(type(self).__name__)
        self._plotters = dict()

    def __getitem__(self, key):
        if key not in plotters.GRAPH_TYPES:
            raise KeyError("Unhandled graph type '%s'" % key)
        if not self._plotters.get(key):
            self._plotters[key] = plotters.__getattribute__(key)(self._graph)
        return self._plotters[key]
