# -*- coding: utf-8 -*-
################################################
# As seen on Python Pandas <pandas.pydata.org> #
################################################

try:
    import cPickle as pickle
except ImportError:
    import pickle

__all__ = ['GenericPickler']

def save(obj, path):
    """
    Pickle (serialize) object to input file path

    Parameters
    ----------
    obj : any object
    path : string
        File path
    """
    f = open(path, 'wb')
    try:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    finally:
        f.close()

def load(path):
    """
    Load pickled pandas object (or any other pickled object) from the specified
    file path

    Parameters
    ----------
    path : string
        File path

    Returns
    -------
    unpickled : type of object stored in file
    """
    f = open(path, 'rb')
    try:
        return pickle.load(f)
    finally:
        f.close()

class GenericPickler(object):
    """ Simple common interface to hadle pickling and unpickling.
    Every class that need to be saved as a pickle should subclass this.
    """
    
    def save(self, file):
        """ Save objet as a pickle """
        save(self, file)

    @staticmethod
    def load(file):
        """ Load object from a pickle """
        return load(file)

