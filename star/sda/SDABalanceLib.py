# -*- coding: utf-8 -*-
import sys
import os
import pandas
import decimal
from datetime import date

#BASEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__),os.path.pardir))
#sys.path.append(BASEPATH)
#sys.path = list(set(sys.path))

# BASEPATH = "/home/contabilita/star_branch"
# sys.path.append(BASEPATH)
# sys.path = list(set(sys.path))

import star.sda as sda

def str2list(string):
    string=string.replace("'","")
    string=string.replace(" ","")
    ret_list = [i for i in string[1:len(string)-1].split(',')]
    return ret_list

def CreDatYear (YEAR, periodDf,moveLineDf,accountDf,DIZP1M1,TUTPDC, contiIfoDf, taxonomyDf, maxLevel):
    ''' Questa funzione calcola per un dato anno, la struttura dati che deve essere inserita in un bilancio
        Gli argomenti di questa funzione sono
        YEAR            Anno dei dati di bilancio elaborati
        perriodDf       DF contenente i metadati sui peeriodi
        moveLineDf      DF contenente i dati delle linee delle scritture contabili
        accountDf       DF contenente i metadati sui conti
        DIZP1M1         Dizionario con i segni relativi per il calcolo dei saldi
        TUTPDC          DF con i metadati sui piani dei conto IV Dir Cee e Goal e tabella di raccordo
        contiIfoDf      DF con la struttura del piano dei conti IV Dir Cee
    '''
    #calcolo data fine anno fiscale
    fiscalyearName=YEAR
    df0 = periodDf[periodDf["NAM_FY"]==fiscalyearName]
    df1 = df0[["FY_DATE_STOP"]].drop_duplicates().reset_index()
    fiscalyearEndDate = df1["FY_DATE_STOP"][0]
    nextFiscalyearEndDate = date(fiscalyearEndDate.year+1,12,31)
    #calcolo saldi divisi in "entro esercizio" e "oltre esercizio"
    #considero le moveline che hanno anno fiscale a quello "desiderato"
    #considero solo le variabili di interesse:
    #   COD_CON		Codice Conto
    #   DBT_MVL		Importo in Dare
    #   CRT_MVL		Importo in Avere
    #   DAT_MVL		Data di registrazione
    #   DAT_DUE		Data di termine dei crediti e debiti
    df2 = moveLineDf.ix[moveLineDf["NAM_FY"]==fiscalyearName].reset_index(drop=True)
    #tolgo le scritture di chiusura del bilancio
    df2 = df2.ix[df2["TYP_JRN"]!="situation"].reset_index(drop=True)
    df2 = df2[['COD_CON','DBT_MVL','CRT_MVL','DAT_MVL','DAT_DUE']]
    #Assegno alla data di termine la data di registrazione quando la data di termine è nulla
    df2['DAT_DUE'][df2['DAT_DUE'].isnull()] = df2['DAT_MVL'][df2['DAT_DUE'].isnull()]
    #Inizializzo a False una variabile strumentale NEXT
    #poi assegno alla variabile NEXT il valore True quando la data di termine è superiore alla fine dell'anno fiscale successivo
    df2['NEXT'] = False
    df2['NEXT'][df2["DAT_DUE"]>nextFiscalyearEndDate] = True
    #Unisco il dataframe con i dati contabili al dataframe con l'informazione sui conti
    df3 = pandas.merge(df2,accountDf,on="COD_CON")
    #Trasformo in float i valori di Dare e Avere
    #df3['DBT_MVL'] = df3['DBT_MVL'].map(float)
    #df3['CRT_MVL'] = df3['CRT_MVL'].map(float)
    df3=df3[["COD_CON","NEXT",'DBT_MVL','CRT_MVL']]
    #sommo gli importi relativi a ciascun conto e considero solo le variabili Importo in dare e Importo in avere
    df4 = df3.groupby(['COD_CON','NEXT']).sum().reset_index()
    df4=df4[["COD_CON","NEXT",'DBT_MVL','CRT_MVL']]
    #unisco i dataframe dei dati Importi con il DF con informazioni sui conti
    df4 = pandas.merge(df4,accountDf,on="COD_CON")
    df4=df4[["COD_CON","NEXT",'DBT_MVL','CRT_MVL','GOV_CON']]
    df4=df4[df4['GOV_CON']!="Transitori"]
    #Costruisco il saldo tra dare e avere, tenendo conto delle diverse aree del piano dei conti.
    #Pertanto per i conti dell'attivo dello stato patrimoniale il saldo sarà calcolato come Dare-Avere,
    # per i conti  del passivo dello stato patrimoniale il saldo sarà calcololto come Avere - Dare ,   e così via.
    #Utilizzo il "barbatrucco" di definire Avere-Dare come -1*(Dare-Avere).
    #Quindi sevo asociare un valore 1 ai conti il cui saldo voglio sia Dare - Avere e
    # devo associare un valore -1 ai conti il cui saldo voglio sia Avere-Dare
    # Utilizzo la variabile P1M1 per contenere questi valori.
    # Per costruire questa variabile ed associarla a df4, utilizzo il dizionario DIZP1M1:
    #--------------------------------------
    df4['P1M1']=df4['GOV_CON'].map(DIZP1M1)
    df4['SALDO']=df4['P1M1']*(df4['DBT_MVL']-df4['CRT_MVL'])
    df4 = df4[["SALDO","COD_CON","NEXT"]]
    df7 = pandas.merge(df4,TUTPDC, on="COD_CON",how="right")
    #tengo solo le variabili che ci servono
    #SALDO       Importo dei vari conti
    #cee_code    Codice conto IV D. CEE
    #name        Descrizione del conto IV D. CEE
    #sign        segno algebrico con cui il conto entra nei processi di aggregazione
    #to discompose  Valore booleano che segnala se gli importi devono essere scomposti per data di scadenza
    #NEXT       Valore booleano che indica se la data di scadenza è superiore al 31.12 dell'anno successivo alla chiusura del bilancio
    df7 = df7[['SALDO','cee_code','name','sign','to_discompose','NEXT']]
    #sommo i diversi importi per conto IV D. CEE, considerando il segno corretto
    df7['SALDO']=df7['SALDO'].map(float)
    df7['SALDO'] = df7['SALDO'] * df7['sign']
    df8 = df7.groupby(['cee_code',"NEXT"]).sum().reset_index()
    df8=df8[["cee_code","NEXT","SALDO"]]
    #unisco ai valori calcolati le informazioni ricavate dalla struttura complessiva della IV D. CEE
    df9 = pandas.merge(df8,contiIfoDf,left_on="cee_code",right_on="code")
    #isolo i casi in cui il conto deve essere scomposto in etro e oltre l'esercizio successivo,
    #e la data di scadenza è superiore all'esercizio successivo
    df10 = df9[(df9["to_discompose"]==True) & (df9["NEXT"]==True)].reset_index()
    #aggiungo alla descrizione delle righe individuate l'indicazione "EsigibiliOltreEsercizioSuccessivo"
    df10['name'] = df10['name']+"EsigibiliOltreEsercizioSuccessivo"
    #isolo i casi in cui il conto deve essere scomposto in etro e oltre l'esercizio successivo,
    #e la data di scadenza è incluso nell'esercizio successivo
    df11 = df9[(df9["to_discompose"]==True) & (df9["NEXT"]==False)].reset_index()
    #aggiungo alla descrizione delle righe individuate l'indicazione "EsigibiliEntroEsercizioSuccessivo"
    df11['name'] = df11['name']+"EsigibiliEntroEsercizioSuccessivo"
    #prendo i conti che non devono essere dictinti tra entro e oltre l'esercizio successivo
    df12 = df9[df9["to_discompose"]==False].reset_index()
    #concateno i df che contengono le tre parti in cui è stato distinto il bilancio:
    # 1) parte con i conti relativi all'esigibilità oltre l'esercizio successivo
    # 2) parte con i conti relativi all'esigibilità entro l'esercizio successivo
    # 3) parte con i conti da non dividere
    df13 = pandas.concat([df10,df11,df12]).reset_index()
    df13 = df13[["name","SALDO"]]
    #unisco il df con i dati di bilancio al df della tassonomia
    #pongo a zero gli importi dei conti rispetto ai quali non ci sono stati movimenti di bilancio
    totalsDf = pandas.merge(df13,taxonomyDf, on="name", how='right')
    totalsDf["USED_FOR_CALC"] = False
    totalsDf["SALDO"][totalsDf["SALDO"].isnull()] = 0
    #ciclo per il calcolo del saldo dei conti della gerarchia
    for i in range(maxLevel):
        #print "level=%s" % i
        df18 = totalsDf[(totalsDf["SALDO"]!=0) & (totalsDf["USED_FOR_CALC"]==False)]
        totalsDf["USED_FOR_CALC"][(totalsDf["SALDO"]!=0) & (totalsDf["USED_FOR_CALC"]==False)] = True
        #print "usati per il calcolo"
        #print df18[["name","SALDO"]]
        if len(df18)>0:
            #aggrego i dati per parent superiore
            df19 = df18.groupby(['cal_parent']).sum()[['SALDO']].reset_index()
            df19 = df19.rename(columns={'cal_parent' : 'name'})
            #print "saldi calcolati"
            #print df19
            if len(df19)>0:
                #effettuo queste istruzioni solo nel caso in cui la sommatoria ha prodotto un risultato
                #aggiungo i dati 'sommatoria' calcolati alla struttura di bilancio completa
                totalsDf = pandas.merge(totalsDf,df19,on="name",how="left")
                #riporto nell'unica variabile SALDO i dati che il merge ha messo in saldo x e y
                totalsDf["SALDO.y"][totalsDf["SALDO.y"].isnull()] = 0
                totalsDf["SALDO"] = totalsDf["SALDO.x"] + totalsDf["SALDO.y"]
                del totalsDf["SALDO.x"]
                del totalsDf["SALDO.y"]
        #print "df finale"
        #print totalsDf
    totalsDf=totalsDf.sort(columns=['_OR_'])
    totalsDf=totalsDf.reset_index(drop=True)
    return totalsDf



def LevBalSec(DIZ1,DESEC,COSEC):
    '''Questa funzione scende lungo i rami dell'ambero della sttruttura dei conti,
        per infividuare il livello a cui è posizionato ciascun conto
    '''
    #inizailizzo la lista finale dei conti
    LCFIN=[]
    #inizializzo la lista finale dei livelli
    LCLIV=[]
    #estraggo dal dizionario della struttura la "radice"
    LC1=DIZ1[DESEC]
    #individuo i "figli" della radice
    LC1=str2list(LC1)
    #includo la radice nella lista finale dei conti e dei livelli
    LCFIN.append(DESEC)
    LCLIV.append(0)
    #print('Liv 1', LC1)
    #inizio ciclo per figli radice
    for I1 in range(len(LC1)):
        #inserisco i figli nella lista finale dei conti e dei livelli
        LCFIN.append(LC1[I1])
        LCLIV.append(1)
        #individuo i "figli" dei "figli"
        LC2=DIZ1[LC1[I1]]
        #costruisco la lista dei "figli" dei "figli"
        LC2=str2list(LC2)
        #print ('Liv 2', LC2)
        #controllo che la lista dei "figli" dei "figli" non sia vuota
        if LC2[0]!="":
            #ripeto tutte le fasi del livello 1 per il livello 2 e così via
            for I2 in range(len(LC2)):
                LCFIN.append(LC2[I2])
                LCLIV.append(2)
                LC3=DIZ1[LC2[I2]]
                LC3=str2list(LC3)
                #print ('Liv 3', LC3)
                if LC3[0]!="":
                    for I3 in range(len(LC3)):
                        LCFIN.append(LC3[I3])
                        LCLIV.append(3)
                        LC4=DIZ1[LC3[I3]]
                        LC4=str2list(LC4)
                        #print ('Liv 4', LC4)
                        if LC4[0]!="":
                            for I4 in range(len(LC4)):
                                LCFIN.append(LC4[I4])
                                LCLIV.append(4)
                                LC5=DIZ1[LC4[I4]]
                                LC5=str2list(LC5)
                                #print ('Liv 5', LC5)
                                if LC5[0]!="":
                                    for I5 in range(len(LC5)):
                                        LCFIN.append(LC5[I5])
                                        LCLIV.append(5)

    DFLIV=pandas.DataFrame({'name':LCFIN, 'lev1':LCLIV})
    DFLIV['SEC']=COSEC
    return DFLIV

def LevBal(taxonomyDf):
    ListNam=taxonomyDf['name'].tolist()
    ListChl=taxonomyDf['children'].tolist()
    DIZ1=dict(zip(ListNam,ListChl))
    SP=LevBalSec(DIZ1, "StatoPatrimoniale","SP")
    CE=LevBalSec(DIZ1, "ContoEconomico","CE")
    TOT=pandas.concat([SP,CE])
    NewtaxonomyDf=pandas.merge(taxonomyDf,TOT, on=['name'])
    NewtaxonomyDf=NewtaxonomyDf.sort(['_OR_'])
    NewtaxonomyDf['NewLab']=NewtaxonomyDf['lev1'].map(lambda x: x*"ZZZZ")+NewtaxonomyDf['label']
    return NewtaxonomyDf

