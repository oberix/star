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
                ax.relim()
            ret.append(
                ax.plot(self._graph._lax, yvals, color=col.get('color', None))
            )
            
        xticklabels = self._graph._x_meta[0]['ticklabels']
        if len(xticklabels) != len(self._graph._lax):
            xticklabels = self._graph._lax
        ax.set_xticklabels(xticklabels)

        return ret

class AbstractBar(BasePlotter):

    WIDTH_FACTOR = 0.9

    def _plot(self, ax, left, height, width, bottom, **kwargs):
        raise NotImplementedError

    def _set_ticks(self, ind, ax, width, sided):
        raise NotImplementedError

    def _twin_ax(self, ax, col):
        raise NotImplementedError

    def plot(self, ax, cols):
        ret = []
        sided = {}
        length = len(self._graph._lax)
        # Organize columns by relative positions
        cols.sort(key=lambda x: x['cumulate'])
        for col in cols:
            self._twin_ax(ax, col)
            if bool(col['cumulate']):
                sided[col['cumulate'][-1]].append(col)
            else:
                sided[col['key']] = [col]
        # bar width
        width = (self._graph._lax.max() - self._graph._lax.min()) /\
                len(self._graph._lax) * self.WIDTH_FACTOR
        if len(sided) > 0:
            width /= len(sided)
                        
        # Build the bars
        ind = np.arange(length)
        for i, lst in enumerate(sided.values()): # each sided
            for j, col in enumerate(lst): # each cumulated
                vals = self._graph._df[col['key']]
                bottom = np.array([0.0]*len(self._graph._lax))
                for base in lst[0:j]:
                    bottom += self._graph._df[base['key']]
                ret.append(
                    self._plot(ax, ind+(i*width), vals, width,
                               bottom=bottom, color=col['color'])
                )
        self._set_ticks(ax, ind, width, sided)
        return ret

class Bar(AbstractBar):
    
    def _plot(self, ax, left, height, width, bottom, **kwargs):
        return ax.bar(left, height, width, bottom=bottom, **kwargs)

    def _set_ticks(self, ax, ind, width, sided):
        # x ticks & labels
        ax.set_xticks(ind + (width * len(sided) / 2.0))
        xticklabels = self._graph._x_meta[0]['ticklabels']
        if len(xticklabels) != len(self._graph._lax):
            xticklabels = self._graph._lax
        ax.set_xticklabels(xticklabels)

    def _twin_ax(self, ax, col):
        if col.get('ax') == 'dx':
            ax = ax.twinx()
            ax.relim()

class Barh(AbstractBar):
    
    def _plot(self, ax, left, height, width, bottom, **kwargs):
        return ax.barh(left, height, height=width, left=bottom, **kwargs)

    def _set_ticks(self, ax, ind, width, sided):
        # y ticks & labels
        ax.set_yticks(ind + (width * len(sided) / 2.0))
        yticklabels = self._graph._x_meta[0]['ticklabels']
        if len(yticklabels) != len(self._graph._lax):
            yticklabels = self._graph._lax
        ax.set_yticklabels(yticklabels)

    def _twin_ax(self, ax, col):
        if col.get('ax') == 'dx':
            ax = ax.twiny()
            ax.relim()

class ErrBar(Bar):

    def _plot(self, ax, left, height, width, bottom, **kwargs):
        return ax.bar(left, height, width, bottom=bottom, yerr=np.std(height), **kwargs)

class ErrBarh(Barh):

    def _plot(self, ax, left, height, width, bottom, **kwargs):
        return ax.barh(left, height, height=width, left=bottom, xerr=np.std(height), **kwargs)
