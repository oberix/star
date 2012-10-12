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
from base_plotter import BasePlotter

class Plot(BasePlotter):
    ''' The most simple of the Simples :) 
    Implement a line plot.
    ''' 

    def plot(self, ax, col):
        ret = ax.plot(self._graph._lax, self._graph._df[col['key']],
                       color=col['color'])

        if col.get('ax') == 'dx':
            ax = ax.get_figure().add_axes(
                ax.get_position(True), 
                label=col['label'],
                frameon=False,
                sharex=ax)
            ax.yaxis.tick_right()
        ax.relim()
        ax.autoscale_view(tight=False, scalex=True, scaley=True)

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
        width = (float(self._graph._lax.max()) - float(self._graph._lax.min())) / float(len(self._graph._lax))
        margin = (0.2 * width)
        dim = width - margin
        border = dim + margin

        # Generate graph calling template method.
        ret = self._plot(ax, col, color=col['color'], align='center', bottom=bottom, dim=dim, border=border)

        ax.relim()
        ax.autoscale_view(tight=False, scalex=True, scaley=True)

        return ret

class Bar(AbstractBar):
    ''' Simple Bar graph, it support cumulative data.
    ''' 

    def _plot(self, ax, col, **kwargs):
        ret = ax.bar(self._graph._lax, self._graph._df[col['key']],
                      color=kwargs['color'], align=kwargs['align'],
                      bottom=kwargs['bottom'], width=kwargs['dim'])

        if col.get('ax') == 'dx':
            ax = ax.get_figure().add_axes(
                ax.get_position(True), 
                label=col['label'],
                frameon=False,
                sharex=ax)
            ax.yaxis.tick_right()

        return ret

class Barh(AbstractBar):
    ''' Horizontal Bar graph, it support cumulative data.
    ''' 

    def _plot(self, ax, col, **kwargs):
        ret = ax.barh( self._graph._lax, self._graph._df[col['key']],
                       color=kwargs['color'], align=kwargs['align'],
                       left=kwargs['bottom'], height=kwargs['dim'])

        if col.get('ax') == 'dx':
            ax = ax.get_figure().add_axes(
                ax.get_position(True), 
                label=col['label'],
                frameon=False,
                sharey=ax,)
            ax.xaxis.tick_top()

        return ret
    





