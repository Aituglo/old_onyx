# -*- coding: utf-8 -*-
"""
Onyx Project
https://onyxlabs.fr
Software under licence Creative Commons 3.0 France
http://creativecommons.org/licenses/by-nc-sa/3.0/fr/
You may not use this software for commercial purposes.
@author :: Cassim Khouani
"""

import os
from os.path import join, expanduser, isdir

__author__ = 'jdorleans'


class FileSystemAccess(object):
    """
    A class for providing access to the onyx FS sandbox. Intended to be
    attached to skills
    at initialization time to provide a skill-specific namespace.
    """
    def __init__(self, path):
        self.path = self.__init_path(path)

    @staticmethod
    def __init_path(path):
        if not isinstance(path, str) or len(path) == 0:
            raise ValueError("path must be initialized as a non empty string")
        path = join(expanduser('~'), '.onyx', path)

        if not isdir(path):
            os.makedirs(path)
        return path

    def open(self, filename, mode):
        """
        Get a handle to a file (with the provided mode) within the
        skill-specific namespace.

        :param filename: a str representing a path relative to the namespace.
            subdirs not currently supported.

        :param mode: a file handle mode

        :return: an open file handle.
        """
        file_path = join(self.path, filename)
        return open(file_path, mode)

    def exists(self, filename):
        return os.path.exists(join(self.path, filename))
