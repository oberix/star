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
import numpy
import pandas
#La data è un oggetto, quindi importo dalla libreria datetime, la funzione data
from datetime import date

# Definizione di costanti:                                                        
# tutto ciò che non verrà modificato dall'esecuzione del codice, ma il cui        
# cambiamento potrebbe essere cruciale per determinarne il comportamento). E'     
# consuetudine distiguere queste vaiabili da quelle 'di elaborazione' scrivendole 
# tutte in maiuscolo.                                                             
PKL_PATH = '/home/contabilita/Goal-PKL/'
COMPANY = 'Vicem'
OUT_PATH = '/home/contabilita/star_branch/sre/libro_giornale/'

PC='PI/CF 03119971202'
ADR= 'Via Santo Stefano 57'
CAP='40125 Bologna'
FY = 2011

# librerie di star 
import sda
from share import Bag
from share import Stark

# Carico un oggetto Stark da un file pickle.                                     
# L'istruzione os.path.join serve a concatenare più parti di un path             
# (/home/contabilita; star_branch/sre; esempio'); è facile cascare in     
# errori facendo una semplice concatenazione di stringhe, quindi si consiglia di 
# usare questo metodo per concatenare diverse parti di un path.  
                
ST01 = Stark.load(os.path.join(PKL_PATH, COMPANY, 'MVL.pickle'))

# Estraggo il DataFrame dall'oggetto Stark e lo salvo in DF01
DF01 = ST01.DF

#considero un sottoinsieme di DF01, estaendo solo le variabili di interesse
DF01 = DF01[['DAT_MVL','NAM_PAR', 'NAM_MVL','COD_CON','NAM_MOV','NAM_CON','DBT_MVL','CRT_MVL',]]

#Creo e definisco gli oggetti data inizio e data fine
#SD = start date
#ED = end date 
#FY = year 

#Generalizzo la gestione delle date di estrazione
SD = date(FY,01,01)
ED = date(FY,12,31)

#Estraggo le moveline di un determinato periodo di tempo, in questo caso di un anno, quindi compresi tra start date e end date, come sopra definite e definisco la nuova variabile come DF02

DF02=DF01[(DF01['DAT_MVL'] >= SD) & (DF01['DAT_MVL'] <= ED)]

#Definisco il commando di ordinamento, ordinando prima per ordine cronologico, ed in seguito per nome di move, in modo da avere ordinate tutte le move che corrispondono ad una determinata data. 

DF03=DF02.sort(columns=['DAT_MVL', 'NAM_MOV'])

DF03=DF03.reset_index(drop=True)
DF03=DF03.reset_index(drop=False)

#Estraggo un dataframe con due colonne: la data delle moveline e il nome dei move (per essere sicuri di conservare l'ordine cronologico)

MOV01=DF03[['index','DAT_MVL','NAM_MOV']]


#Attribuisco una serie di progressivi al dataframe così creato, attribuendo numeri che partono da 1 e "saltando" le ripetizioni di NAM_MOV

PROG=MOV01['NAM_MOV'].tolist()
LPROG=[]
PREC="INIZIO"
CONT=1
for I in range(len(PROG)):
	if PROG[I]==PREC:
		LPROG.append("")
	else:
            LPROG.append(str(CONT))
    	CONT=CONT+1
	PREC=PROG[I]


MOV01['PROG'] = LPROG
MOV01=MOV01[['index','PROG']]
	


#La variabile 'NOM_MOV' è replicata più volte per la stessa moveline. Quindi, aggrego la stessa, eliminando tutte le righe con lo stesso numero di move, appartenenti alla stessa data. 

#MOV02 = MOV01.drop_duplicates(cols=['DAT_MVL','NAM_MOV'])


#Creo una lista/serie di numeri progressivi che cominciano con 1 e finiscono seguendo la lunghezza del DF MOV02 (+1 si mette perché l'estremo destro del range è sempre escluso

#LISTPROG=range(1,len(MOV02)+1)


# Attribuisco al dataframe MOV02, la lista dei progressivi, appena creata
#MOV02['PROG'] = LISTPROG

#Faccio il merge tra il MOV02 e il DF03 che è già ordinato per ordine cronologico, con tutte le variabili di interesse. La chiave del merge sarà sempre, sia la data, che in nome del move. 

DF04=pandas.merge(DF03,MOV01,on=['index'],how='left')
del DF04['index']


#Riscrivo la data senza l'anno

DF04['DAT_MVL'] = DF04['DAT_MVL'].map(lambda x : x.strftime('%d-%m'))

# Creo un dizionario LM (descrive il layout della tabella).                     
# Le barre verticali "|" indicano quali separatori disegnare; i numeri a fianco 
# dell'indicazione dell'allineamento sono le dimensioni relativi delle colonne  
# (0.5 metà delle altre colonne; 2 doppio delle altre colonne, etc.)            
lm = {
    'DAT_MVL': [0,   '|0.5c|'  , '|Data|'],
    'PROG':    [1,   '0.1c|'  , 'Nr.|'],
    'NAM_PAR': [2,   '1.5c|'  ,  'Partner|'],
    'COD_CON': [3,   '0.6c|'  , 'Cod. Conto|'],
    'NAM_CON': [4,   '1.5l|'  ,  'Conto|'],
    'NAM_MVL': [5,   '1.5l|'  , 'Descrizione|'],
    'DBT_MVL': [6,   '0.75r|'  , 'Dare|'],
    'CRT_MVL': [7,   '0.75r|'  , 'Avere|'],
}

# Creo un oggetto Bag usando come Dataframe df, come LM lm e come TITLE 'Libro
# Giornale'. Il parametro TIP='tab' indica al sistema che si intende generare
# una tabella da questi dati, presto sarà supportato anche TIP='graph' per
# generare un grafico.
BG01 = Bag(DF04, os.path.join(OUT_PATH, 'table0.pickle'), LM=lm, TITLE='Libro Giornale', TI='tab')
BG01.year = FY
BG01.company = COMPANY +' Srl'
BG01.partiva = PC
BG01.address = ADR
BG01.cap = CAP


# Infine salvo l'oggetto bag in un file pickle
BG01.save()


# Rimane solamente da generare il report con SRE :) 
# Per farlo, andate nella cartella sre ed eseguite  
# $ python sre.py esempio                    

# Happy coding!
