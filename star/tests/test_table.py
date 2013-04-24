# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
import pandas

# star_path = path della directroy principale
star_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.path.pardir,
                                         os.path.pardir))
if star_path in sys.path:
    # rimuoviamo tutte le occorrenze di star_path
    sys.path = [p for p in sys.path if p != star_path]
# inseriamo star_path in seconda posizione, la prima dovrebbe essere riservata
# alla cartella corrente in cui è poisizionato il file
sys.path.insert(1, star_path)
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
    lm = {
        'A': [0, '|c', '|A'],
        'B': [1, '|c', 'B'],
        'C': [2, '|c|', 'C|'],
    }

    df = pandas.DataFrame({
        'A': np.random.rand(10) * 100000,
        'B': np.random.rand(10) * 100000,
        'C': np.random.rand(10) * 100000,
    })

    base = '/tmp/test/'
    if not os.path.isdir(base):
        os.makedirs(base)

    mybag = Bag(df, lm=lm, stype='tab')
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
