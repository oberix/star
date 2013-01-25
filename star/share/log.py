# -*- coding: utf-8 -*-
# pylint: disable=C0103
##############################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Bardelli (<marco.bardelli@aderit.it>)
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
'''Logging system for STAR'''

# usage for users:
# ---
# from star.share.log import getLogger
# logger = getLogger(__name__)
# #### or ####
# class Klass(object):
#     def __init__(self, *args, *kwargs):
#         self._logger = getLogger(type(self).__name__)
# ---
# to re/configure logging system via dictConfig use:
# from star.share.log import configure_logging
# configure_logging(logging_dict={...}, config_filename='/path/to/cfg')

import logging
from logging.config import (fileConfig as log_fileConfig,
                            dictConfig as log_dictConfig)
from logging import getLogger as _getLogger


__all__ = ['getLogger', 'configure_logging']

### maybe to move in star.share.defaults ???
DEFAULT_LOGGING_DICT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    },
    'formatters':{
        'brief': { 'format': "%(name)s: %(message)s"},
        'normal': { 'format': "%(name)s:%(levelname)s: %(message)s"},
        'verbose': {
            'format': "%(asctime)s %(name)-15s:%(levelname)-8s: %(message)s",
            'datefmt': "%d-%m-%Y %H:%M:%S",
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
        },
        'console.error': {
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
            'level': 'ERROR',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
        },
    },
    'loggers': {
        'py.warnings': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
    'root': {
            'handlers': ['console'],
            'level': 'NOTSET',
            'propagate': False,
    }
}


def configure_logging(logging_dict=None, config_filename=None,
                      cfg_disable_existing_loggers=True):
    '''
    Configure logging library.

    @logging_dict: is a dict to quickly update defaults,
                   see logging.config.dictConfig
    @config_filename: is a path to a ConfigParser-like file with
                      section [formantters],[handlers],[loggers] etc,
                      see logging.config.fileConfig
    @cfg_disable_existing_loggers: if True (default), disable defaults.

    @logging_dict has precedence over @config_filename.
    '''
    ## copied from django.conf.__init__.LazySettings._configure_logging
    try:
        # Route warnings through python logging
        logging.captureWarnings(True)
        # Allow DeprecationWarnings through the warnings filters
        logging.warnings.simplefilter("default", DeprecationWarning)
    except AttributeError:
        # No captureWarnings on Python 2.6, DeprecationWarnings are on anyway
        pass

    log_dictConfig(DEFAULT_LOGGING_DICT_CONFIG)

    if config_filename:
        from ConfigParser import NoSectionError, NoOptionError
        _disable_loggers = cfg_disable_existing_loggers
        try:
            log_fileConfig(config_filename,
                           disable_existing_loggers=_disable_loggers)
        except (NoSectionError, NoOptionError):  #, err:
            # logging.error("Parsing %s for logging configuration: %s",
            #            config_filename, err)
            pass

    if logging_dict:
        log_dictConfig(logging_dict)

    configure_logging.yet_configured = True


def getLogger(name=None):
    '''
    Wrap logging.getLogger to preconfigure logging library.
    '''
    if not getattr(configure_logging, 'yet_configured', False):
        configure_logging()
    return _getLogger(name)
