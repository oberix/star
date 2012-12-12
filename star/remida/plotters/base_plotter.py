# -*- coding: utf-8 -*-

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


        
