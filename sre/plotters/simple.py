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

import numpy as np
import math
from base_plotter import BasePlotter

class Plot(BasePlotter):
    ''' The simpler of Simples :) 
    Implement a line plot.
    ''' 

    def plot(self, ax, col):
        yvals = self._graph._df[col['key']]
        if col.get('ax') == 'dx':
            ax = ax.twinx()
        ret = ax.plot(self._graph._lax, yvals, color=col.get('color', None), zorder=10)
        # ax.relim()
        # ax.autoscale_view(tight=False, scalex=True, scaley=True)
        self._logger.debug('ret = %s', [l.get_zorder() for l in ret])
        self._graph._set_x_ax(ax)
        return ret

class AbstractBar(BasePlotter):
    ''' Abstract class implementing those procedures that are commont both to
    Bar an Horizonta bar (Barh) graphics
    '''
    
    def __init__(self, graph):
        super(AbstractBar, self).__init__(graph)
        self._bottom = 0

    def _plot(self, ax, col, **kwargs):
        ''' Template method: must be overridden by subclasses to make the real
        plotting.
        '''
        raise NotImplementedError
    
    def plot(self, ax, col):
        ''' Plotting function.
        '''
        bottom = None
        # set cumulative data start
        if col.get('cumulate'):
            bottom = np.array([0.0]*len(self._graph._lax))
            for key in col['cumulate']:
                bottom += self._graph._df[key]

        # compute margins
        width = (self._graph._lax.max() - self._graph._lax.min()) / len(self._graph._lax)
        margin = (0.2 * width)
        dim = width - margin
        border = dim + margin

        # Generate graph calling template method.
        ret = self._plot(ax, col, color=col.get('color', None), align='center',
                         bottom=bottom, dim=dim, border=border)
        return ret

class Bar(AbstractBar):
    ''' Simple Bar graph, it support cumulative data.
    ''' 

    def _plot(self, ax, col, **kwargs):
        yvals = self._graph._df[col['key']]

        if col.get('ax') == 'dx':
            ax = ax.twinx()
        ret = ax.bar(self._graph._lax, yvals,
                     color=kwargs['color'], align=kwargs['align'],
                     bottom=kwargs['bottom'], width=kwargs['dim'],
                     zorder=0, rasterized=True, alpha=0.8)
#        ax.relim()
        # ax.autoscale_view(tight=False, scalex=True, scaley=True)
        self._logger.debug('ret = %s', [p.get_zorder() for p in ret])
        self._graph._set_x_ax(ax)
        return ret

class Barh(AbstractBar):
    ''' Horizontal Bar graph, it support cumulative data.
    ''' 

    def _plot(self, ax, col, **kwargs):
        yvals = self._graph._df[col['key']]
        if col.get('ax') == 'dx':
            ax = ax.twinx()
        ret = ax.barh( self._graph._lax, self._graph._df[col['key']],
                       color=kwargs.get('color', None), align=kwargs.get('align', None),
                       left=kwargs.get('bottom', None), height=kwargs.get('dim', None),
                       zorder=1)
        return ret
