# -*- coding: utf-8 -*-

import numpy as np
from star.remida.plotters.base_plotter import BasePlotter

class Plot(BasePlotter):
    ''' The simpler of Simples :) 
    Implement a line plot.
    ''' 
    def plot(self, ax, cols):
        ret = []
        for col in cols:
            yvals = self._graph._df[col['key']]
            if col.get('ax') == 'dx':
                ax = ax.twinx()
            ret.append(
                ax.plot(self._graph._lax, yvals, color=col.get('color', None), zorder=10))
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
    
    def plot(self, ax, cols):
        ''' Plotting function.
        '''
        ret = []
        for col in cols:
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
            ret.append(self._plot(ax, col, color=col.get('color', None), align='center',
                                  bottom=bottom, dim=dim, border=border))
        return ret

class Barh(AbstractBar):
    ''' Horizontal Bar graph, it support cumulative data.
    ''' 

    def _plot(self, ax, col, **kwargs):
        yvals = self._graph._df[col['key']]
        if col.get('ax') == 'dx':
            ax = ax.twinx()
        ret = ax.barh(self._graph._lax, self._graph._df[col['key']],
                       color=kwargs.get('color', None), align=kwargs.get('align', None),
                       left=kwargs.get('bottom', None), height=kwargs.get('dim', None),
                       zorder=1)
        return ret

class Bar(BasePlotter):
    
    WIDTH_FACTOR = 0.9

    def plot(self, ax, cols):
        ret = []
        # need to separate cumulated from sided columns
        sided = {}
        # cumulated = []
        length = len(self._graph._lax)
        cols.sort(key=lambda x: x['cumulate'])
        for col in cols:
            if bool(col['cumulate']):
                sided[col['cumulate'][-1]].append(col)
            else:
                sided[col['key']] = [col]
        # bar width
        width = (self._graph._lax.max() - self._graph._lax.min()) /\
                len(self._graph._lax) * self.WIDTH_FACTOR
        if len(sided) > 0:
            width /= len(sided)
                        
        # build the bars
        ind = np.arange(length)
        for i, lst in enumerate(sided.values()):
            for j, col in enumerate(lst): 
                vals = self._graph._df[col['key']]
                bottom = np.array([0.0]*len(self._graph._lax))
                for base in lst[0:j]:
                    bottom += self._graph._df[base['key']]
                ret.append(
                    ax.bar(ind+(i*width), vals, width, bottom=bottom, color=col['color'])
                )

        # x ticks & labels
        ax.set_xticks(ind + (width * len(sided) / 2.0))
        xticklabels = self._graph._x_meta[0]['ticklabels']
        if len(xticklabels) != len(self._graph._lax):
            xticklabels = self._graph._lax
        ax.set_xticklabels(xticklabels)

        return ret
