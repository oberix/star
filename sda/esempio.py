# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

##############################################################################
# Questo è un programma di esempio, mostra i passaggi fondamentali necessari #
# per:                                                                       #
#     - caricare un oggetto Stark da un file pickle                          #
#     - costruire un oggetto Bag                                             #
#     - salvare l'oggetto Bag in un file pickle                              #
#                                                                            #
# Il file generato è pronto per essere dato in pasto alla procedura sre per  #
# lagenerazione dei report.                                                  #
##############################################################################

# librerie standard
import os
import sys
# pandas non è usato direttamente in questo esempio, ma in genere sarà utile
import pandas 

# Definizione di costanti:                                                        
# tutto ciò che non verrà modificato dall'esecuzione del codice, ma il cui        
# cambiamento potrebbe essere cruciale per determinarne il comportamento). E'     
# consuetudine distiguere queste vaiabili da quelle 'di elaborazione' scrivendole 
# tutte in maiuscolo.                                                             
LIB_PATH = '/home/contabilita/star_branch/'
PKL_PATH = '/home/contabilita/Goal-PKL/'
COMPANY = 'Vicem'
OUT_PATH = '/home/contabilita/star_branch/sre/esempio/'

# Indico a python dove si trovano le librerie di star:                         
# sys.path è una comune lista di stringhe, ciascuna delle quali rappresenta un 
# path, un percorso all'interno del filesystem; quando si esegue l'istruzione  
# "import", Python cerca in tutti questi percorsi per trovare il file (modulo) 
# richiesto.                                                                   
sys.path.append(LIB_PATH)

# librerie di star
from share import Bag
from share import Stark

# Carico un oggetto Stark da un file pickle.                                     
# L'istruzione os.path.join serve a concatenare più parti di un path             
# (/home/contabilita; star_branch/sre; esempio'); è facile cascare in     
# errori facendo una semplice concatenazione di stringhe, quindi si consiglia di 
# usare questo metodo per concatenare diverse parti di un path.                  
ST01 = Stark.load(os.path.join(PKL_PATH, COMPANY, 'MVL.pickle'))

# Estraggo il DataFrame dall'oggetto Stark e lo salvo in df
DF01 = ST01.DF

#considero un sottoinsieme di df, estaendo solo le variabili di interesse
DF01=DF01[['DAT_MVL','COD_CON','NAM_CON','NAM_PAR','DBT_MVL','CRT_MVL',]]

# Creo un dizionario LM (descrive il layout della tabella).                     
# Le barre verticali "|" indicano quali separatori disegnare; i numeri a fianco 
# dell'indicazione dell'allineamento sono le dimensioni relativi delle colonne  
# (0.5 metà delle altre colonne; 2 doppio delle altre colonne, etc.)            
lm = {
    'DAT_MVL': [0,   '|  c|'  , '|@v0|', '|Data|'],
    'COD_CON': [4,   '   l|'  , '|@v0|', ' Codice Conto|'],
    'NAM_CON': [5,   '  2l|'  , ' @v2|', ' Conto|'],
    'NAM_PAR': [2,   '  2l|'  , '|@v0|', ' Partner|'],
    'DBT_MVL': [6,   '0.5r|'  , ' @v2|', ' Dare|'],
    'CRT_MVL': [7,   '0.5r|'  , ' @v2|', ' Avere|'],
}

# Creo un oggetto Bag usando come Dataframe df, come LM lm e come TITLE 'Libro
# Giornale'. Il parametro TIP='tab' indica al sistama che si intende generare
# una tabella da questi dati, presto sarà supportato anche TIP='graph' per
# generare un grafico.
BG01 = Bag(DF=DF01, LM=lm, TITLE='Libro Giornale', TIP='tab')

# Infine salvo l'oggetto bag in un file pickle
BG01.save(os.path.join(OUT_PATH, 'table0.pickle'))

# Rimane solamente da generare il report con SRE :) 
# Per farlo, andate nella cartella sre ed eseguite  
# $ python sre.py esempio                    

# Happy coding!
