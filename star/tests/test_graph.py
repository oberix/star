import os
import numpy as np
import pandas as pnd
from star.share.bag import Bag

def curpath():
    pth, _ = os.path.split(os.path.abspath(__file__))
    return pth

if __name__ == '__main__':
    lm_bar = {
        'a': {'type': 'lax',
              'label': 'AAA'},
        'b': {'type': 'bar',
              'label': 'BBB',
              'color': 'b',},
        'c': {'type': 'bar',
              'ax': 'dx',
              'label': "CCC",
              'color': 'g',
              'cum': 'b'},
        }

    lm_barh = {
        'a': {'type': 'lax',
              'label': 'AAA',
              'ticklabel': 'd',
          },
        'b': {'type': 'barh',
              'ax': 'sx',
              'label': 'BBB',
              'color': 'b'},
        'c': {'type': 'barh',
              'ax': 'dx',
              'label': "CCC",
              'color': 'g',
              'cum': 'b'},
        }

    lm_plot = {
        'a': {'type': 'lax',
              'label': 'AAA'},
        'b': {'type': 'bar',
              'ax': 'sx',
              'label': 'BBB',
              'color': 'b'},
        'c': {'type': 'plot',
              'ax': 'dx',
              'label': "CCC",
              'color': 'g',}
        }

    df = pnd.DataFrame({
        'a': np.arange(0, 11, 1),
        'b': np.arange(5, 16, 1),
        'c': np.arange(0, 5.5, 0.5),
        'd': ['a','b','c', 'd', 'e', 'f', 'g', 'h', 'i','l', 'm']
    })

    lm_sc = {
        'a': {'type': 'lax',
              'ax': 'sx',
              'label': 'AAA'},
        'b': {'type': 'scatter',
              'ax': 'sx',
              'label': 'BBB',
              'colnnnor': 'b'},
        }

    df_sc = pnd.DataFrame({
            'a': [59.9, 46.2, 0],
            'b': [13.6, 7.1, 2],
            })

    bar = Bag(df, lm=lm_bar, stype='graph', title='USRobotics',
              size='stamp',
              legend=True,
              fontsize=10.0)
    barh = Bag(df, lm=lm_barh, stype='graph', title='USRobotics',
              size='stamp',
              legend=True,
              fontsize=10.0)
    plot = Bag(df, lm=lm_plot, stype='graph', title='USRobotics',
              size='stamp',
              legend=True,
              fontsize=10.0)
    scat = Bag(df_sc, lm=lm_sc, stype='graph', title='USRobotics',
              size='stamp',
              legend=False,
              fontsize=10.0)

    bar.save(os.path.join(curpath(), "../reports/esempio/bar.pickle"))
    barh.save(os.path.join(curpath(), "../reports/esempio/barh.pickle"))
    plot.save(os.path.join(curpath(), "../reports/esempio/plot.pickle"))
    scat.save(os.path.join(curpath(), "../reports/esempio/scatter.pickle"))
