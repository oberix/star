# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
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

import ConfigParser
from optparse import OptionParser
import logging
import os
import sys

# Dirr path to configuration file(s)
CONFIG_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(sys.argv[0])),
        os.path.pardir, 'config'))

# Map loglevel's names and values
LEVELS_NAMES = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG')
LOGLEVELS = dict([(x, getattr(logging, x)) for x in LEVELS_NAMES])

# Some defaults
DEF_CONFIG = os.path.join(CONFIG_PATH, 'config.cfg')
DEF_DB = os.getenv('LOGNAME')
DEF_HOST = 'localhost'
DEF_PORT = 5432

__all__ = ['Config', 'CONFIG_PATH']

class Config(object):
    """ Generic class to handle configuration parameters, it provides common
    parameters for any script of this suite, such as db conection parameters.

    Config is capable of handling relative paths only when they are placed
    inside CONFIG_PATH base path; to make Config aware that an option is a
    path, just put it undet 'path' section in your config file.
    """

    def __init__(self, filename=DEF_CONFIG, *args, **kwargs):
        """ Initialize the following instance attribute:
        
        - db_options : database connection parameter
        - options : options dictionary
        - configfile : path to configuration file

        @ param filename: configuration file's path
        """
        self.config_file = filename
        self.options = {
            'database' : DEF_DB,
            'host': DEF_HOST,
            'port': DEF_PORT,
            'username': None,
            'password': None,
            }
        self._parser = self._init_parser()

    # def __repr__(self):
    #     """ Print options dictionary instead of object. """
    #     return "db_options = %s"%(repr(self.db_options))

    # non-public methods

    def _makeabs(self, path):
        """ make a path relative to CONFIG_PATH an absolute one. 
        @ param path: path to convert
        @ return: absolute path
        """
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(CONFIG_PATH, path))

    def _init_parser(self):
        """ Create an option parser and add options to it.
        If you need to add other options just extend this method.
        """ 
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config", 
                          help="specify alternate config file")
        parser.add_option("-d", "--dbname", dest = "database", 
                          help="specify the dbname", 
                          default=os.getenv('LOGNAME'))
        parser.add_option("-u", "--username", dest="username", 
                          help="specify username for connecting to db", 
                          default=None)
        parser.add_option("-p", "--password", dest="password", 
                          help="specify the password for connecting to db", 
                          default=None)
        parser.add_option("-H", "--host", dest="host", 
                          help="specify the host in which it's present the db", 
                          default=DEF_HOST)
        parser.add_option("-P", "--port", dest="port", 
                          help="specify the port for connecting to db", 
                          default=DEF_PORT)
        parser.add_option('--log-level', dest='logLevel', type='choice', 
                          choices=LOGLEVELS.keys(), 
                          help='specify the level of the logging. Accepted values: %s' % \
                              str(LOGLEVELS.keys()),
                          default=logging.INFO)
        return parser

    def _read_config(self):
        """ Read configuration file and and save values inside internal
        dictionaries. Try to make anything under 'path' section an absolute
        path.
        """
        p = ConfigParser.ConfigParser()
        p.optionxform = str
        if p.read([self.config_file]):
            for section in p.sections():
                for (name, value) in p.items(section):
                    if section == 'paths':
                        value = self._makeabs(value)
                    self.options[name] = value
                    
    # Public methods

    def parse(self):
        """ Joins options from cli an config file. 
        Command line arguments override config files values.
        """
        (opts, ar) = self._parser.parse_args()
        if opts.ensure_value('config', False):
            self.config_file = os.path.abspath(opts.config)
        self._read_config()        
        for key in ar:
            self.options[key] = opts.ensure_value(key, False)
        self.options['logLevel'] = opts.logLevel

