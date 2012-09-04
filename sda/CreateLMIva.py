# -*- coding: utf-8 -*-
lm_registri_iva = {
        'DATE': [0, 'c', 'Data registrazione'],
        'M_NUM': [1, 'c', 'Numero protocollo'],
        'DATE_DOC': [2, 'c', 'Data documento'],
        'M_REF': [3, 'c', 'Numero documento'],
        'PARTNER': [4, 'c', 'Controparte'],
        'T_NAME': [5, 'c', 'Tipo imposta'],
        'BASE': [6, 'r', 'Imponibile'],
        'TAX': [7, 'r', 'Imposta'],
        }
        
lm_riepiloghi_iva = {
        'TEXT': [0, 'c', "@v1","",],
        'T_NAME': [1, 'c', "@v1","Tipo imposta"],
        'BASE_DEB': [2, 'r', 'Iva a debito',"Imponibile"],
        'TAX_DEB': [3, 'r', 'Iva a debito',"Imposta"],
        'BASE_CRED': [4, 'r', 'Iva a credito',"Imponibile"],
        'TAX_CRED': [5, 'r', 'Iva a credito',"Imposta"],
        }
        
lm_pagamenti_iva_differita = {
        'DAT_PAY': [0, 'c', 'Data incasso o pagamento'],
        'NAM_SEQ': [1, 'c', 'Registro IVA'],
        'NAM_MOV': [2, 'c', 'Numero protocollo'],
        'DAT_MVL': [3, 'c', 'Data registrazione'],
        'NAM_PAR': [4, 'c', 'Controparte'],
        'NAM_TAX': [5, 'c', 'Tipo imposta'],
        'AMO': [6, 'r', 'Imposta'],
        }
        
lm_da_pagare_iva_differita = {
        'NAM_SEQ': [0, 'c', 'Registro IVA'],
        'NAM_MOV': [1, 'c', 'Numero protocollo'],
        'DAT_MVL': [2, 'c', 'Data registrazione'],
        'NAM_PAR': [3, 'c', 'Controparte'],
        'NAM_TAX': [4, 'c', 'Tipo imposta'],
        'AMO': [5, 'r', 'Imposta'],
        }