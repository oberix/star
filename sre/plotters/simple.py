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

from base_graph import BaseGraph

class Plot(BaseGraph):

    def plot(self, ax, col):
        return ax.plot(self._graph._lax, self._graph._df[col['key']],
                       color=col['color'])

class Bar(BaseGraph):

    def plot(self, ax, col):
        return ax.bar(self._graph._lax, self._graph._df[col['key']],
               color=col['color'], align='center')

class Barh(BaseGraph):

    def plot(self, ax, col):
        return ax.barh(self._graph._lax, self._graph._df[col['key']],
               color=col['color'], align='center')
