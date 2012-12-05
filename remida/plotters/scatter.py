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
import matplotlib.patches as patches
from base_plotter import BasePlotter

WORST_COLOR = "#FFDBC1"
BEST_COLOR = "#9BFFE6"
#BEST_COLOR = "#005e93"

class Scatter(BasePlotter):
    ''' Implement a benckmark scatter graphic.
    '''
    
    def plot(self, ax, col):
        x_data = self._graph._lax
        y_data = self._graph._df[col['key']]
        x_meta = self._graph._x_meta[0]
        # TODO: set lable for the axes
        val = (x_data[0], y_data[0])
        bench = (x_data[1], y_data[1])
        quadrant = (x_data[2], y_data[2])
        # TOCHECK: log looks good, but it's just empirical
        margin = (np.log1p(np.abs(x_data[0:2].max() - x_data[0:2].min())), 
                  np.log1p(np.abs(y_data[0:2].max() - y_data[0:2].min())))
        min_val = (x_data[0:2].min() - margin[0], y_data[0:2].min() - margin[0])
        max_val = (x_data[0:2].max() + margin[1], y_data[0:2].max() + margin[1])

        # Draw colored quadrants
        for idx, quad in enumerate(quadrant):
            if quad < 2: # 2 right quadrants
                rect_x = bench[0]
                width = max_val[0] - bench[0]
            else:  # 2 left quadrants
                rect_x = min_val[0]
                width = bench[0] - min_val[0]
            if quad == 1 or quad == 2: # 2 lower quadrants
                rect_y = min_val[1]
                height = bench[1] - min_val[1]
            else: # 2 upper quadrants
                rect_y = bench[1]
                height = max_val[1] - bench[1]
            color = WORST_COLOR
            if idx == 0:
                color = BEST_COLOR
            rect = patches.Rectangle(
                (rect_x, rect_y), width=width, height=height, antialiased=True,
                facecolor=color, zorder=1)
            ax.add_patch(rect)
        # Draw dot
        scat = [ax.scatter(val[0], val[1], s=20, c=col['color'],
                          color=col['color'], antialiased=True, zorder=3)]
        
        offset = (margin[0]/15.0, margin[1]/15.0)
        # Add a lable to the dot
        # TODO: this string should be escaped
        label = ax.text(val[0] + offset[0], val[1] + offset[1], self._graph._title,
                        color=col['color'], clip_on=False, zorder=4)
        ax.add_artist(label)

        # bechmark axes
        ax.axvline(x = bench[0], linewidth=2, linestyle='--', 
                   color='MidnightBlue', antialiased=True, zorder=2)
        ax.axhline(y = bench[1], linewidth=2, linestyle='--',
                   color='MidnightBlue', antialiased=True, zorder=2)
        
        # Set axes tiks, limit and labels
        ax.set_xlim((min_val[0], max_val[0]))
        ax.set_xticks([bench[0], val[0]])
        ax.set_ylim((min_val[1], max_val[1]))
        ax.set_yticks([bench[1], val[1]])
        # TODO: this strings should be escaped too
        xlab = ax.set_xlabel(x_meta['label'], color='DarkBlue', labelpad=-1)
        ylab = ax.set_ylabel(col['label'], color='DarkBlue', labelpad=-1)
        
        # FIME: isn't there a better way to avoid axes labels to fall off the
        # figure?
        ax.get_figure().subplots_adjust(right=0.750, left=0.175, 
                                        top=0.950, bottom=0.150)
        return scat
