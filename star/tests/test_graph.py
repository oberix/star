import os
import numpy as np
import pandas
from star.share.bag import Bag
from star.remida.remida import sre

TEMPLATE = '''
\\documentclass[a4paper, 10pt]{article}
\\usepackage{graphicx, caption, subcaption}

\\newcommand{\\SRE}[1]{\\textit{insert[#1]}}

\\begin{document}

\\section*{Graph test}

\\begin{figure}[h!]
  \\begin{subfigure}[cm]{0.5\\linewidth}
    \\SRE{bar}
  \\end{subfigure}
  ~
  \\begin{subfigure}[cm]{0.5\\linewidth}    
      \\SRE{barh}
  \\end{subfigure}
  \\\\
  \\begin{subfigure}[cm]{0.5\\linewidth}    
      \\SRE{plot}
  \\end{subfigure}
  ~ 
  \\begin{subfigure}[cm]{0.5\\linewidth}    
      \\SRE{scatter}
  \\end{subfigure}
\\end{figure}

\\end{document}
'''

if __name__ == '__main__':

    lm_bar = {'graph': 
              {'vars': {
                  'a': {'type': 'lax',
                        'label': 'AAA'},
                  'b': {'type': 'bar',
                        'label': 'BBB',
                        'color': 'b',},
                  'c': {'type': 'bar',
                        'ax': 'sx',
                        'label': "CCC",
                        'color': 'g',
                        'cumulate': 'b'},
              }}}

    lm_barh = {'graph': 
               {'vars': {
                   'a': {'type': 'lax',
                         'label': 'AAA',
                         'ticklabel': 'd',},
                   'b': {'type': 'barh',
                         'ax': 'sx',
                         'label': 'BBB',
                         'color': 'b'},
                   'c': {'type': 'barh',
                         'ax': 'sx',
                         'label': "CCC",
                         'color': 'g',
                         'cumulate': 'b'},
               }}}

    lm_plot = {'graph': 
               {'vars': {
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
               }}}

    # df = pandas.DataFrame({
    #     'a': np.arange(0, 11, 1),
    #     'b': np.arange(5, 16, 1),
    #     'c': np.arange(0, 5.5, 0.5),
    #     'd': ['a','b','c', 'd', 'e', 'f', 'g', 'h', 'i','l', 'm']
    # })

    df = pandas.DataFrame({
        'a': np.arange(0, 10, 1),
        'b': np.random.rand(10),
        'c': np.random.rand(10),
        'd': np.random.rand(10),
    })


    lm_sc = {'graph': 
             {'vars': {
                 'a': {'type': 'lax',
                       'ax': 'sx',
                       'label': 'AAA'},
                 'b': {'type': 'scatter',
                       'ax': 'sx',
                       'label': 'BBB',
                       'color': 'b'},
             }}}

    df_sc = pandas.DataFrame({
            'a': [59.9, 46.2, 0],
            'b': [13.6, 7.1, 2],
            })

    plot = Bag(df, md=lm_plot, stype='graph')
    bar = Bag(df, md=lm_bar, stype='graph')
    barh = Bag(df, md=lm_barh, stype='graph')
    scat = Bag(df_sc, md=lm_sc, stype='graph')

    base = '/tmp/test/'
    if not os.path.isdir(base):
        os.makedirs(base)

    plot.save(os.path.join(base, "plot.pickle"))
    bar.save(os.path.join(base, "bar.pickle"))
    barh.save(os.path.join(base, "barh.pickle"))
    scat.save(os.path.join(base, "scatter.pickle"))

    fd = open(os.path.join(base, 'main.tex'), 'w')
    try:
        fd.write(TEMPLATE)
    finally:
        fd.close()

    # # Generate config file (not mandatory)
    # fd = open(os.path.join(base, 'config.cfg'), 'w')
    # try:
    #     fd.write('[paths]\n')
    # finally:
    #     fd.close()

    sre(base)
