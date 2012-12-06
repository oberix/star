# -*- coding: utf-8 -*-
import sys
import os
import getopt
import pandas
import decimal
import numpy
from datetime import date

# Servabit libraries

import star.sda as sda
import SDABalanceLib
from star.share import Config
from star.share import Stark
from star.share import Bag

OUT_PATH = '/home/contabilita/star_branch/sre/bilancio/'
#-----------------------------------------------------------------------------------------------------------
#
#                   Parte del programma relativa a tutti gli anni
#
#----------------------------------------------------------------------------------------------------------

# local libs (librerie locali)
PathCsv="/home/contabilita/star_branch/config/SDABalance/"
#legge il file config
configFilePath = os.path.join(BASEPATH,"config","balance.cfg")
config = Config(configFilePath)
config.parse()
#assegna ai parametri di interesse il valore letto in config
comNam=config.options.get('company',False)
picklesPath = config.options.get('pickles_path',False)
fiscalyearName=config.options.get('fiscalyear',False)
#verifica che la stringa associata al parametro only_validated_moves inserita in config
#sia effettivamente un valore boleano
onlyValML=True
if str(config.options.get('only_validated_moves',True))=='False':
    onlyValML=False

#lettura degli oggetti stark di interesse
companyPathPkl = os.path.join(picklesPath,comNam)
moveLineStarK = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
moveLineDf = moveLineStarK.df
accountStarK = Stark.load(os.path.join(companyPathPkl,"ACC.pickle"))
accountDf = accountStarK.df
periodStarK = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
periodDf = periodStarK.df

#leggo il file csv contenente la mappatura tra il piano dei conti Servabit e la IV Direttiva CEE e calcolo del saldo dei conti foglia
corrispIfoDf = pandas.read_csv(PathCsv+"corrisp_ifo.csv", sep=",", header=0)
contiIfoDf = pandas.read_csv(PathCsv+"conti_ifo.csv", sep=",", header=0)
tuttoIfoDf = pandas.merge(corrispIfoDf,contiIfoDf,left_on="cee_code",right_on="code")
del tuttoIfoDf["code"]
#unisco il df della descrizione della IV D. CEE con il df di corrispondenza tra IV D. CEE e PdC Goal
# tengo le seguenti variabiabili
#   cee_code        Codice conto IV D. CEE
#   name            Descrizione del conto IV D. CEE
#   sign            segno algebrico con cui il conto entra nei processi di aggregazione
#   to discompose   Valore booleano che segnala se gli importi devono essere scomposti per data di scadenza
#   COD_CON         Condice conto PdC Goal
TUTPDC = pandas.merge(accountDf,tuttoIfoDf,left_on="COD_CON",right_on="servabit_code")
TUTPDC = TUTPDC[['cee_code','name','sign','to_discompose',"COD_CON"]]
#Costruzione del dizionario dei fattori (-1 e +1) necessari al calcolo del SALDO
DIZP1M1={
    "Fondi"                                     : -1,
    'Crediti di funzionamento'                  : +1,
    'Immobilizzazioni'                          : +1,
    unicode('Altre Attività',encoding='utf-8')  : +1,
    'Patrimonio Netto'                          : -1,
    unicode('Altre Passività', encoding='utf-8'): -1,
    'Debiti di funzionamento'                   : -1,
    'Costi'                                     : +1,
    'Ricavi'                                    : -1   }

#lettura dei csv della tassonomia e calcolo livello massimo della gerarchia dei conti cee
taxonomyDf = pandas.read_csv(PathCsv+"chart_ese.csv", sep=",", header=0)
# teniamo le variabili che ci servono
# abstract          identifica i conti Etichetta
# children          contiene la lista dei conti "figli"
# name              variabile identificativa del conto
# label             etichetta di stampa
# parent            conto padre
# cal_parent        conto padre utilzzato per le somme
# level             livello di profondità delle gerarchia, utilizzato perle somme
#_OR_               l'ordine dei conti nella stampa del bilancio
taxonomyDf=taxonomyDf[['abstract','children','name','label','parent','cal_parent','level','_OR_']]
#individuo il grado più profondo del livello della tassonomia
DF1 = taxonomyDf[["level"]]
DF1 = DF1[DF1["level"].notnull()].drop_duplicates()
maxLevel = int(max(list(DF1["level"])))
#elimino dalla tassonomia i conti che non devono essere stampati nel bilancio

#costruisco la struttura del bilancio idonea alla stampa
UNO=SDABalanceLib.LevBal(taxonomyDf)
#estraggo i dati di bilancio 2010
Y2010=SDABalanceLib.CreDatYear ('2011', periodDf,moveLineDf,accountDf,DIZP1M1,TUTPDC, contiIfoDf, taxonomyDf, maxLevel)
Y2010=Y2010[['name','SALDO']]
Y2010=Y2010.rename(columns={'SALDO':'2010'})
#estraggo i dati di bilancio 2011
Y2011=SDABalanceLib.CreDatYear ('2011', periodDf,moveLineDf,accountDf,DIZP1M1,TUTPDC, contiIfoDf, taxonomyDf, maxLevel)
Y2011=Y2011[['name','SALDO']]
Y2011=Y2011.rename(columns={'SALDO':'2011'})
#combino i tre df
FINDF=pandas.merge(UNO,Y2010, on=['name'])
FINDF=pandas.merge(FINDF,Y2011, on=['name'])
FINDF=FINDF[['_OR_','NewLab','2011','2010']]
FINDF=FINDF.sort(['_OR_'])
#sostituiamo nelle colonne dei saldi gli zeri con None
FINDF['2011'] = numpy.where(FINDF['2011'] > 0,  FINDF['2011'], None)
FINDF['2010'] = numpy.where(FINDF['2010'] > 0,  FINDF['2010'], None)
#sostituiamo le Z nelle colonne dei nomi dei conti con degli spazi vuoti
FINDF['NewLab']=FINDF['NewLab'].map(lambda s: s.replace('Z', '\hspace*{2pt}'))
FINDF = FINDF.reset_index(drop=True)
#cerchiamo l'indice che corrisponde alla riga 'Conto economico'
indexCE = int(FINDF.ix[FINDF['NewLab'] == 'Conto economico'].index)
#dividiamo il dataframe in due: uno che comprende lo stato patrimoniale, uno per il conto economico
dfSP = FINDF[:indexCE]
dfCE = FINDF[indexCE:]

# Creo un dizionario LM (descrive il layout della tabella).
# Le barre verticali "|" indicano quali separatori disegnare; i numeri a fianco
# dell'indicazione dell'allineamento sono le dimensioni relativi delle colonne
# (0.5 metà delle altre colonne; 2 doppio delle altre colonne, etc.)
lm = {
    'NewLab': [0,'4l','@v0',],
    '2011': [1,'r','2011',],
    '2010': [2,'r','2010',],
    }

# Creo un oggetto Bag usando come Dataframe df, come LM lm e come title 'Libro
# Giornale'. Il parametro TIP='tab' indica al sistama che si intende generare
# una tabella da questi dati, presto sarà supportato anche TIP='graph' per
# generare un grafico.
BG01 = Bag(dfSP, os.path.join(OUT_PATH, 'StaPatr.pickle'),
           meta=lm, title="Stato Patrimoniale", bag_type='tab')
BG02 = Bag(dfCE, os.path.join(OUT_PATH, 'ConEco.pickle'),
           meta=lm, title="Conto Economico", bag_type='tab')

anag = Bag(pandas.DataFrame(),
           os.path.join(OUT_PATH, 'anag.pickle'),
           title='Dati anagrafici',
           ragsoc='Studiabo Srl')
# Infine salvo l'oggetto bag in un file pickle
BG01.save()
BG02.save()
anag.save()


