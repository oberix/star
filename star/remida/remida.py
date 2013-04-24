#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import logging

import template

# star_path = path della directroy principale
star_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.path.pardir,
                                         os.path.pardir))
if star_path in sys.path:
    # rimuoviamo tutte le occorrenze di star_path
    sys.path = [p for p in sys.path if p != star_path]
# inseriamo star_path in seconda posizione, la prima dovrebbe essere riservata
# alla cartella corrente in cui è poisizionato il file
sys.path.insert(1, star_path)
from star.share.config import Config


__all__ = ['sre']

_logger = None


def _load_config(src_path, confpath=None):
    ''' Get configuration file.

    @ param src_path: project source directory
    @ param confpath: path to the configuration file
    @ return: options dictionary

    '''
    if confpath is None:
        confpath = os.path.join(src_path, 'config.cfg')
    if not os.path.isfile(confpath):
        logging.warning('No config file found in %s', confpath)
        # return {}
    config = Config(confpath)
    config.parse()
    logging.debug(config)
    return config.options


def _compile_tex(file_, template, dest, fds):
    ''' Compile LaTeX, calls texi2dvi via system(3)

    @ param file_: main .tex file path
    @ param template: template file path, used to handle output names
    @ param dest: output file path
    @ params fds: list of temporary files'es file descriptors, we need to close
        them in order to have them removed before terminating.
    @ return: texi2dvi exit code.

    '''
    pdf_out = os.path.basename(template).replace('.tex', '.pdf')
    # create output dir if it does not exist
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    command = [
        "texi2dvi",
        "--pdf",
        "--batch",
        "--clean",
        "-o", os.path.join(dest, pdf_out),  # output file
        "-I", os.path.dirname(template),  # input path (where other files resides)
        file_,  # main input file
        ]
    _logger.info("Compiling into PDF.")
    _logger.debug(" ".join(command))
    # open log file
    logfd = open(template.replace('.tex', '.log'), 'w')
    try:
        ret = subprocess.call(command, stdout=logfd, stderr=logfd)
    except IOError, err:
        _logger.error(err)
        return err.errno
    finally:
        logfd.close()
    # close temporary files (those created by TexGraph), causing deletion.
    for fd in fds:
        fd.close()
    if ret > 0:
        _logger.warning(
            "texi2pdf exited with bad exit status, you can inspect what went "
            "wrong in %s",
            os.path.join(dest, file_.replace('.tex', '.log')))
        return ret
    _logger.info("Done.")
    return ret


def sre(src_path, config=None, **kwargs):
    ''' Main procedure to generate a report.
    Besically the procedure is splitted into these steps:
        - load configuration file
        - load template
        - load bags
        - build the report

    In most cases every file needed to build the report is stored in the same
    directory (src_path); anyway, if a configuration file is present inside the
    src_path, it can be used to specicy different parameters.

    @ param src_path: project source path.
    @ param config: a configuration file (if None, the one inside src_path will
        be used).
    @ return: _report() return value

    '''
    config = _load_config(src_path, confpath=config)
    global _logger
    _logger = logging.getLogger('sre')
    templ_file = None
    try:
        templ_file = config['template']
        templ_path = os.path.dirname(templ_file)
    except KeyError:
        if os.path.isfile(os.path.join(src_path, 'main.tex')):
            templ_file = os.path.join(src_path, 'main.tex')
        elif os.path.isfile(os.path.join(src_path, 'main.html')):
            templ_file = os.path.join(src_path, 'main.html')
        templ_path = src_path
    
    # Identify type just from filename suffix
    if templ_file.endswith('.tex'):
        templ = template.TexSreTemplate(os.path.join(templ_path, templ_file),
                                        config=config)
        report, fd_list = templ.report()
        if not isinstance(report, (str, unicode)):
            # Error, return errno
            return report
        return _compile_tex(templ_file.replace('.tex', '_out.tex'), templ_file,
                            os.path.dirname(templ_file), fd_list)
    elif templ_file.endswith('.html'):
        for file_ in os.listdir(templ_path):
            if file_.endswith('.html'):
                templ = template.HTMLSreTemplate(file_, config=config)
                report = templ.report()
                if not isinstance(report, str):
                    # Error, return errno
                    return report
    else:
        _logger.error("Could not find a valid template, exiting.")
        return 1
    return 0
    
if __name__ == "__main__":
    ''' Procedure when executing file. A directory path is needed as first
    argument.
    '''
    if len(sys.argv) < 2:
        logging.error("Specify a path containing report files")
        sys.exit(1)
    sys.exit(sre(sys.argv.pop(1)))
