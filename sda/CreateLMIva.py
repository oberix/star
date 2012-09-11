# -*- coding: utf-8 -*-
lm_registri_iva = {
        'DATE': [0, 'c', 'Data','registrazione'],
        'M_NUM': [1, '0.5c', 'Numero','protocollo'],
        'DATE_DOC': [2, 'c', 'Data ','documento'],
        'M_REF': [3, 'c', 'Numero ','documento '],
        'PARTNER': [4, '1.3c', 'Controparte',"@v3"],
        'T_NAME': [5, '1.5c', 'Tipo','imposta'],
        'BASE': [6, '0.5r', 'Imponibile',"@v1"],
        'TAX': [7, '0.5r', 'Imposta',"@v2"],
        }
        
lm_riepiloghi_iva = {
        'TEXT': [0, '2c', "@v1","@v2",],
        'T_NAME': [1, '2c', "@v1","Tipo imposta"],
        'BASE_DEB': [2, '0.5r', 'Iva a debito',"Imponibile"],
        'TAX_DEB': [3, '0.5r', 'Iva a debito',"Imposta"],
        'BASE_CRED': [4, '0.5r', 'Iva a credito',"Imponibile "],
        'TAX_CRED': [5, '0.5r', 'Iva a credito',"Imposta "],
        }
        
lm_pagamenti_iva_differita = {
        'DAT_PAY': [0, 'c', 'Data incasso',"o pagamento"],
        'SEQUENCE': [1, 'c', 'Registro IVA',"@v1"],
        'M_NUM': [2, 'c', "Numero","protocollo"],
        'DATE': [3, 'c', "Data", "registrazione"],
        'PARTNER': [4, 'c', 'Controparte',"@v2"],
        'T_NAME': [5, '2c', 'Tipo',"imposta"],
        'AMOUNT': [6, '0.5r', 'Imposta',"@v3"],
        }
        
lm_da_pagare_iva_differita = {
        'SEQUENCE': [0, 'c', 'Registro IVA',"@v1"],
        'M_NUM': [1, 'c', 'Numero', 'protocollo'],
        'DATE': [2, 'c', 'Data', 'registrazione'],
        'PARTNER': [3, 'c', 'Controparte',"@v2"],
        'T_NAME': [4, '2c', 'Tipo', 'imposta'],
        'AMOUNT': [5, '0.5r', 'Imposta',"@v3"],
        }
        
lm_riepilogo_differita = {
        'T_NAME': [0, '3l', "@v1"],
        'TEXT': [1, 'l', "@v2"],
        'AMOUNT': [2, '0.5r', 'Imposta'],
        }
        
lm_liquidazione_iva = {
        'TEXT': [0, '2l', "@v1"],
        'SEQUENCE': [1, 'l', "@v2"],
        'DBT': [2, '0.5r', 'Iva a debito'],
        'CRT': [3, '0.5r', 'Iva a credito'],
        }
        
lm_controllo_esercizio = {
        'TEXT': [0, '4l', "@v1"],
        'DBT': [1, '0.5r', 'Iva a debito'],
        'CRT': [2, '0.5r', 'Iva a credito'],
        }