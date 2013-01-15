# -*- coding: utf-8 -*-
import os
import numpy as np
import pandas
from star.share.bag import Bag
from star.remida.remida import sre

TEMPLATE = '''
\\documentclass[a4paper, 10pt]{article}
\\usepackage{longtable}
\\usepackage{tabu}

\\newcommand{\\SRE}[1]{\\textit{insert[#1]}}

\\begin{document}
\\section*{Table test}

 \\begin{center}

    \\SRE{mybag}

\\end{center}

\\end{document}
'''

if __name__ == '__main__':
    md = {'table': {'vars': {
        'A': {'order': 0, 
              'align': 'center', 
              'vsep': 'left', 
              'headers' : 'A'},
        'B': {'order': 1, 
              'align': 'center', 
              'vsep': 'left', 
              'headers' : 'B'},
        'C': {'order': 2, 
              'align': 'center', 
              'vsep': 'right', 
              'headers' : 'C'},
    }}}

    df = pandas.DataFrame({
        'A': np.random.rand(10) * 100000,
        'B': np.random.rand(10) * 100000,
        'C': np.random.rand(10) * 100000,
    })

    base = '/tmp/test/'
    if not os.path.isdir(base):
        os.makedirs(base)

    mybag = Bag(df, md=md, stype='tab')
    mybag.save(os.path.join(base, 'mybag.pickle'))
    fd = open(os.path.join(base, 'main.tex'), 'w')
    try:
        fd.write(TEMPLATE)
    finally:
        fd.close()
    fd = open(os.path.join(base, 'config.cfg'), 'w')
    try:
        fd.write('[paths]\n')
    finally:
        fd.close()
    sre(base)

