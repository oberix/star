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
import os
import select
import logging
import multiprocessing

# creiamo il logger multiprocessing
log_format = "%(asctime)s %(levelname)s %(message)s"
fmt = logging.Formatter(log_format)
hconsole = logging.StreamHandler()
hconsole.setFormatter(fmt)
logger = logging.getLogger("parallel_jobs")
logger.setLevel(logging.INFO)
logger.addHandler(hconsole)

def do_jobs_efficiently(processes=None):
    if processes is None:
        processes = []
    
    if not isinstance(processes, (list, tuple)):
        logger.error("l'argomento 'procesess' deve essere una lista/tupla di "
                     "coppie processo/argomenti")
        return

    njobs = multiprocessing.cpu_count() + 1
    logger.info('njobs = %d', njobs)
    child_fd = -1
    parent_fd = -1
    parent_stream = None
    child_pids = []
    rfds = []
    streams = []
    for func, args in processes:
        if not callable(func):
            logger.error("la funzione {0} non è una chiamabile".format(func))
            continue
        # IPC init
        if len(child_pids) >= njobs:
            (_rfds,_wfds,_xfds) = select.select(rfds,[],[])
            for done_fd in _rfds:
                idx = rfds.index(done_fd)
                rfds.pop(idx)
                cpid = child_pids.pop(idx)
                os.waitpid(cpid, 0)
                stream = streams.pop(idx)
                assert(len(rfds) == len(child_pids))
                assert(len(child_pids) == len(streams))
                out_raw = stream.readline()
                stream.close()
                del stream
                logger.debug("P child({0}) say: {1}".format(cpid, out_raw[:-1]))
        assert(len(rfds) == len(child_pids))
        if len(child_pids) < njobs:
            (parent_fd, child_fd) = os.pipe()
            pid = os.fork()
            if pid == 0:
                # sono il figlio
                assert(child_fd > -1)
                assert(parent_fd > -1)
                logger.debug("in child: fd={0}" .format(child_fd))
                my_pid = os.getpid()
                os.close(parent_fd)
                ## faccio l'effetivo lavoro
                try:
                    if isinstance(args, (list, tuple)):
                        func(*args)
                    elif isinstance(args, dict):
                        func(**args)
                    else:
                        func(args)
                finally:
                    ## comunico la fine del lavoro
                    os.write(child_fd, "({0})\n".format(my_pid))
                    os.close(child_fd)
                    os._exit(os.EX_OK)
            else:
                parent_stream = os.fdopen(parent_fd, 'r')
                os.close(child_fd)
                child_pids.append(pid)
                rfds.append(parent_fd)
                streams.append(parent_stream)
    while len(child_pids) > 0:
        (_rfds,_wfds,_xfds) = select.select(rfds,[],[])
        for done_fd in _rfds:
            idx = rfds.index(done_fd)
            rfds.pop(idx)
            cpid = child_pids.pop(idx)
            os.waitpid(cpid, 0)
            stream = streams.pop(idx)
            assert(len(rfds) == len(child_pids))
            assert(len(child_pids) == len(streams))
            out_raw = stream.readline()
            stream.close()
            del stream
            logger.debug("P child({0}) say: {1}".format(cpid, out_raw[:-1]))
