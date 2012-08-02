# -*- coding: utf-8 -*-
lm_registri_iva = {
        'DAT_MVL': [0, 'c', 'Data registrazione',None,None],
        'NAM_MOV': [1, 'c', 'Numero protocollo',None,None],
        'DAT_DOC': [2, 'c', 'Data documento',None,None],
        'REF_MOV': [3, 'c', 'Numero documento',None,None],
        'NAM_PAR': [4, 'c', 'Controparte',None,None],
        'NAM_TAX': [5, 'c', 'Tipo imposta',None,None],
        'BASE': [6, 'r', 'Imponibile',None,None],
        'TAX': [7, 'r', 'Imposta',None,None],
        }
        
lm_pagamenti_iva_differita = {
        'DAT_PAY': [0, 'c', 'Data incasso o pagamento',None,None],
        'NAM_SEQ': [1, 'c', 'Registro IVA',None,None],
        'NAM_MOV': [2, 'c', 'Numero protocollo',None,None],
        'DAT_MVL': [3, 'c', 'Data registrazione',None,None],
        'NAM_PAR': [4, 'c', 'Controparte',None,None],
        'NAM_TAX': [5, 'c', 'Tipo imposta',None,None],
        'AMO': [6, 'r', 'Imposta',None,None],
        }
        
lm_da_pagare_iva_differita = {
        'NAM_SEQ': [0, 'c', 'Registro IVA',None,None],
        'NAM_MOV': [1, 'c', 'Numero protocollo',None,None],
        'DAT_MVL': [2, 'c', 'Data registrazione',None,None],
        'NAM_PAR': [3, 'c', 'Controparte',None,None],
        'NAM_TAX': [4, 'c', 'Tipo imposta',None,None],
        'AMO': [5, 'r', 'Imposta',None,None],
        }