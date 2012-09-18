#!/usr/bin/python
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

__VERSION__ = '0.1'
__AUTHOR__ = 'Luigi Cirillo (<luigi.cirillo@servabit.it>)'


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.url import URL
from datetime import datetime
from decimal import Decimal

import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, Sequence, ForeignKey, Date, Boolean
import logging

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share.config import Config


#genero una classe di nome Base da usare con SQLAlchemy
Base = declarative_base()

configFilePath = os.path.join(BASEPATH,"config","goal2stark.cfg")
conf = Config(configFilePath)
conf.parse()

#definisco una struttura di log per il controllo del programma a video
log_istance =  'DBMapping'
logging.basicConfig(level = conf.options.get('log_level'))
logger = logging.getLogger('DBMapping')


class IrSequence(Base):
    '''Mmappatura della tabella contenente i dati relativi alle sequenza associate ad un journal '''
    __tablename__ = 'ir_sequence'
    
    name = Column(String(64), nullable=False)
    code = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    
    #one2many
    journals = relationship("AccountJournal")
    company = relationship("ResCompany")
    
    
class ResCompany(Base):
    '''Mappatura della tabella contenente i dati relativi ad una company, ossia all'impresa
    di cui il database contiene i dati'''    
    __tablename__ = 'res_company'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    #one2one
    partner = relationship("ResPartner",  primaryjoin="ResCompany.partner_id==ResPartner.id", uselist=False)
    ateco_2007_vat_activity = Column(String(300))
    
        
class ResPartner(Base):
    '''Mappatura della tabella contenente i dati relativi ad un partner
        - nome/ragione sociale
        - partita iva
        - codice fiscale (tax)
        - indirizzi associati al partner
    '''    
    __tablename__ = 'res_partner'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    vat = Column(String(32))
    tax = Column(String(36))
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=True)
    
    #one2one
    company = relationship("ResCompany", primaryjoin="ResCompany.id==ResPartner.company_id")
    #one2many
    addresses = relationship("ResPartnerAddress")
    
    
class ResPartnerAddress(Base):
    '''Mappatura della tabella contenente i dati relativi ad un indirizzo
        - nome identificativo del'indirizzo
        - id del partner
        - via
        - città
        - Codice avviamento postale        
    '''    
    __tablename__ = 'res_partner_address'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    street = Column(String(128))
    city = Column(String(128))
    zip = Column(String(24))
    
    #many2one
    partner = relationship("ResPartner")
        
        
class AccountFiscalyear(Base):
    '''Mappatura della tabella contenente i dati relativi ad un Anno fiscale
        - nome identificativo dell'anno
        - company_id
        - data inizio
        - data fine
    '''    
    __tablename__ = 'account_fiscalyear'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    date_start = Column(Date, nullable=False)
    date_stop = Column(Date, nullable=False)
    
    #one2many
    periods = relationship("AccountPeriod")
    #many2one
    company = relationship("ResCompany")
        
    
class AccountPeriod(Base):
    '''Mappatura della tabella contenente i dati relativi ad un Periodo Fiscale
        - nome identificativo del periodo
        - company_id
        - data inizio
        - data fine
        - special ??????
        - anno fiscale di riferimento
    '''    
    __tablename__ = 'account_period'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    date_start = Column(Date, nullable=False)
    date_stop = Column(Date, nullable=False)
    special = Column(Boolean)
    
    fiscalyear_id = Column(Integer, ForeignKey('account_fiscalyear.id'), nullable=False)
    fiscalyear = relationship("AccountFiscalyear")
    company = relationship("ResCompany")
    
    
class AccountAccountType(Base):
    '''Mappatura della tabella contenente i dati relativi ad tipo di Conto
        - nome identificativo del tipo
        - codice che identifica il tipo
    '''    
    __tablename__ = 'account_account_type'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    code = Column(String(32), nullable=False)
    

class AccountAccount(Base):
    '''Mappatura della tabella contenente i dati relativi al Conto di un piano dei conti
        - nome identificativo del conto 
        - codice che identifica del conto
        - comapny_id
        - riferimento al tipo di conto
        - type ????
        - conto padre
    '''    
    __tablename__ = 'account_account'
    
    name = Column(String(128), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    code = Column(String(64))
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    user_type = Column(Integer, ForeignKey('account_account_type.id'), nullable=False)
    type = Column(String(16), nullable=False)
    parent_id = Column(Integer, ForeignKey('account_account.id'))
    account_type = relationship("AccountAccountType")
    company = relationship("ResCompany")
    parent = relationship("AccountAccount", remote_side=[id])
    
    
class AccountJournal(Base):
    '''Mappatura della tabella contenente i dati relativi al Journal
        - nome identificativo del journal
        - type ????
        - riferimneto alla sequenza aassociata al Journal
    '''    
    __tablename__ = 'account_journal'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    type = Column(String(32), nullable=False)
    
    sequence_id = Column(Integer, ForeignKey('ir_sequence.id'), nullable=False)
    sequence = relationship("IrSequence")


class AccountTax(Base):
    '''Mappatura della tabella contenente i dati relativi alle Imposte/tasse
        - nome identificativo della tassa
        - tax code: è il codice associato alla tassa che nella contabiltà delle tasse riporta l'ammontare d'imposta
        - base code: è il codice associato alla base imponibile che nella contabiltà delle tasse riporta l'ammontare della base imponibile
        - ref tax code: idem che tax code ma riferito ad un reso
        - ref base code: idem che base code ma riferito ad un reso
    '''    
    __tablename__ = 'account_tax'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'))
    
    tax_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    base_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    ref_tax_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    ref_base_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    
    company = relationship("ResCompany")
    
class AccountTaxCode(Base):
    '''Mappatura della tabella contenente i dati relativi Codici della Contabilità delle Tasse/Imposte
        - nome identificativo del Codice
        - id identificatvo
    '''    
    __tablename__ = 'account_tax_code'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True, )

class AccountVoucher(Base):
    '''Mappatura della tabella contenente i dati relativi ad un "Diritto/Impegno di Incasso/Pagamento"
        - nome identificativo del Diritto/Impegno
        - id identificatvo
        - company_id
        - period_id
        - scrittura contabile (relazione meny2one) 
        - partner
        - data di registrazione
        - data di scadenza
        - numero ??
        - stato  : registrato o meno
        - type   ??
        - importo 
    '''    
    __tablename__ = 'account_voucher'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    
    company_id = Column(Integer, ForeignKey('res_company.id'))
    period_id = Column(Integer, ForeignKey('account_period.id'))
    move_id = Column(Integer, ForeignKey('account_move.id'))
    journal_id = Column(Integer, ForeignKey('account_journal.id'), nullable=False)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    date = Column(Date)
    date_due = Column(Date)
    number = Column(String(32))
    state = Column(String(32))
    type = Column(String(16))
    amount = Column(postgresql.NUMERIC, nullable=False)

    partner = relationship("ResPartner",  uselist=False)
    move = relationship("AccountMove",  uselist=False)
    company = relationship("ResCompany")
    period = relationship("AccountPeriod")
    journal = relationship("AccountJournal")


class AccountInvoice(Base):
    '''Mappatura della tabella contenente i dati relativi ad una fattura
        - nome identificativo della fattura
        - id identificatvo
        - company_id
        - period_id
        - scrittura contabile (relazione many2one) 
        - partner
        - data del documento
        - data della fattura - diventer la data di registrazione
        - data di scadenza
        - numero del documento
        - importo 
    '''
    __tablename__ = 'account_invoice'
  
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    
    company_id = Column(Integer, ForeignKey('res_company.id'))
    period_id = Column(Integer, ForeignKey('account_period.id'))
    move_id = Column(Integer, ForeignKey('account_move.id'))
    journal_id = Column(Integer, ForeignKey('account_journal.id'), nullable=False)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    date_document = Column(Date, nullable=False)
    date_invoice = Column(Date)  #inserito da Luigi il 11/7/2011
    date_due = Column(Date)
    number = Column(String(64))
    state = Column(String(16))
    type = Column(String(16))
    amount_total = Column(postgresql.NUMERIC)
    
    move = relationship("AccountMove",  uselist=False)
    partner = relationship("ResPartner",  uselist=False)
    company = relationship("ResCompany")
    period = relationship("AccountPeriod")
    journal = relationship("AccountJournal")

    
class AccountMove(Base):
    '''Mappatura della tabella contenente i dati relativi ad una scrittura (composta da più linee)
        - nome identificativo della scrittura
        - id identificatvo
        - campo testo di contenente riferimenti
        - stato della scrittura: bozza o validata
        - company_id
        - journal_id
        - period_id
        - data di registrazione
        - partner
        - fattura di riferimento
        - da controllare
        - linee della scrittura (relazione one2many)
    '''    

    __tablename__ = 'account_move'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    ref = Column(String(64))
    state = Column(String(16), nullable=False)
    company_id = Column(Integer, ForeignKey('res_company.id'))
    journal_id = Column(Integer, ForeignKey('account_journal.id'), nullable=False)
    period_id = Column(Integer, ForeignKey('account_period.id'), nullable=False)
    date = Column(Date, nullable=False)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    partner = relationship("ResPartner",  uselist=False)
    invoice = relationship("AccountInvoice",  uselist=False)
    to_check = Column(Boolean)
    #amount = Column(Float)
    #one2many
    move_lines = relationship("AccountMoveLine")
    company = relationship("ResCompany")
    period = relationship("AccountPeriod")
    journal = relationship("AccountJournal")
           
class AccountMoveLine(Base):
    '''Mappatura della tabella contenente i dati relativi ad una linea di scrittura
        - nome identificativo della linea
        - id identificatvo
        - campo testo di contenente riferimenti
        - stato della scrittura: bozza o validata
        - company_id
        - journal_id
        - period_id
        - account_id    conto del piano dei conti
        - move_id
        - tax_code_id  questo può essere riferito ad un code di tassa o ad un code di base imponibile

        - riferimento alla riconciliazione
        - riferimento alla riconciliazione parziale

        - partner
        - data di registrazione
        - date di scadenza (quello che in fattura è chiamato date_due)
        - importo a debito
        - importo a credito
        - importo della imposta/tassa o della base imponibile
    '''    
    __tablename__ = 'account_move_line'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    ref = Column(String(64))
    state = Column(String(16))
    
    company_id = Column(Integer, ForeignKey('res_company.id'))
    journal_id = Column(Integer, ForeignKey('account_journal.id'), nullable=False)
    period_id = Column(Integer, ForeignKey('account_period.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account_account.id'), nullable=False)
    move_id = Column(Integer, ForeignKey('account_move.id'), nullable=False)
    tax_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    
    reconcile_id = Column(Integer, ForeignKey('account_move_reconcile.id'), nullable=False)
    reconcile = relationship("AccountMoveReconcile", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_id")
    
    reconcile_partial_id = Column(Integer, ForeignKey('account_move_reconcile.id'), nullable=False)
    reconcile_partial = relationship("AccountMoveReconcile", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_partial_id")
    
    partner_id = Column(Integer, ForeignKey('res_partner.id'))
    
    date = Column(Date, nullable=False)
    date_maturity = Column(Date)
    debit = Column(postgresql.NUMERIC)
    credit = Column(postgresql.NUMERIC)
    tax_amount = Column(postgresql.NUMERIC)
    
    #many2one
    move = relationship("AccountMove")
    journal = relationship("AccountJournal")
    account = relationship("AccountAccount")
    partner = relationship("ResPartner")
    company = relationship("ResCompany")
    period = relationship("AccountPeriod")
    
class AccountMoveReconcile(Base):
    '''Mappatura della tabella contenente i dati relativi alla Riconciliazione
        - nome identificativo della linea
        - id identificatvo
        - tipo
        - riferimento alla linea di registrazione
        - riferimneto della riconciliazione partiale alla linea di registrazione
    '''    
    __tablename__ = 'account_move_reconcile'
    
    name = Column(String(64), nullable=False)
    type = Column(String(16), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    
    lines = relationship("AccountMoveLine", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_id")
    partial_lines = relationship("AccountMoveLine", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_partial_id")


def open_session():
    '''
    open a SQLAlchemy session from informations holded by goal2stark.cfg
    '''
    global conf, logger
    logger.debug('Opening session')
    url = URL(
        '+'.join([conf.options.get('dbtype', 'postgresql'), conf.options.get('driver', 'psycopg2')]),
        username = conf.options.get('user', None),
        password = conf.options.get('pwd', None),
        host = conf.options.get('host', None),
        port = conf.options.get('port', None),
        database = conf.options.get('dbname', None),
        )
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)
    return Session()

def close_session(session,):
    '''
    Close SQLAlchemy session
    '''
    global logger
    logger.debug('Closing session')
    session.close_all()
