# -*- coding: utf-8 -*-

META_PROD = {
    'AREAX': {
        'TYPE': 'D',
        'ORD': 0,
        'child': {
            'XER': {
                'TYPE': 'D'}}},
    'AREAM': {
        'TYPE': 'D',
        'ORD': 1,
        'child': {
            'MER': {
                'TYPE': 'D'}}},
    'YEAR': {
        'TYPE': 'D',
        'ORD': 2},
    'R': {
        'TYPE': 'D',
        'ORD': 3},
    'X': {'TYPE': 'N'},
    'M': {'TYPE': 'N'},
    'K': {'TYPE': 'N'},
    'U': {'TYPE': 'N'},
    'Q': {'TYPE': 'N'}
    }

META_COUNTRY = {
    'UL20': {
        'TYPE': 'D',
        'ORD': 0,
        'child': {
            'UL200': {
                'TYPE': 'D',
                'child': {
                    'UL1000': {
                        'TYPE': 'D',
                        'child': {
                            'UL3000':{
                                'TYPE': 'D'}
                            }
                        }
                    }
                }
            }
        },
    'AREAM': {
        'TYPE': 'D',
        'ORD': 1,
        'child': {
            'MER': {
                'TYPE': 'D'}}},
    'YEAR': {
        'TYPE': 'D',
        'ORD': 2},
    'R': {
        'TYPE': 'D',
        'ORD': 3},
    'X': {'TYPE': 'N'},
    'M': {'TYPE': 'N'},
    'K': {'TYPE': 'N'},
    'U': {'TYPE': 'N'},
    'Q': {'TYPE': 'N'}
    }
