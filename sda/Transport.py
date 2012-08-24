# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Luigi Bidoia (<luigi.bidoia@servabit.it>)
#            Viviana Nero (<viviana.nero@studiabo.it>)    
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
##############################################################################
#
#   Questo programma serve a costruire la classe transport necessaria per 
#   trasportare i dati dalla procedura Ulisse alla procedura Apollo
#
##############################################################################
import sys
import os
import pandas
import logging

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share.generic_pickler import GenericPickler

class Transport(GenericPickler):
    '''
    Questa classe consente di istanziare un oggetto Transport
    costituito dalle seguenti componenti: 
                COD (stringa): identificativo univoco all'interno del dossier
                TIP (stringa): qualifica la tipologia di oggetto grafico
                               può assumere i valori "tab" o "graph"
                TITLE (stringa): titolo dell'oggetto grafico
                DF: dataframe
                LM (lista di dizionari): ciascun dizionario ha come chiave il nome della variabile
                                         e come valori la lista degli header da stampare per quella
                                         variabile
                FOOTNOTE (lista di stringhe): ciascuna stringa contiene una riga di footnote 
    '''   
    
    def __init__(self,COD=None,TIP=None,TITLE=None,DF=None,LM=None,FOOTNOTE=None):
        self.COD=COD
        self.TIP=TIP
        self.TITLE=TITLE
        self.DF=DF
        self.LM=LM
        self.FOOTNOTE=FOOTNOTE

        # Controllo coerenza tra variabili del dataframe e variabili contenute
        # in LM nel caso in cui la tipologia sia quella di una tabella.
        if TIP=="tab":
            try :
                lvar=DF.columns
            except AttributeError:
                print("Warnings: DF non è un Dataframe") 
                # FIXME: this is not safe, the obj is created, but it's
                #        broken. It is better to rise the exception.
                return 
            lvar1=pandas.Index(LM.keys())
            lcheck=lvar-lvar1
            print lcheck
            if lcheck != 0:
                print("Warnings: non c'è coerenza tra le variabili del dataframe e le variabili di LM")
                # FIXME: this is not safe, the obj is created, but it's
                #        broken. It is better to rise the exception.
                return
