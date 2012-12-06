# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
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

STYPES = ('elab', 'tab', 'graph')

from star.share.config import *
from star.share.generic_pickler import *
from star.share.stark import *
from star.share.bag import *





import os
import sys

share_dir_path = os.path.dirname(os.path.dirname(__file__))
if not share_dir_path in sys.path:
    sys.path.insert(0, share_dir_path)
