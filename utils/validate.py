# Copyright 2021, Battelle Energy Alliance, LLC

import os
import errno
import logging
import configparser


def validate_extension(extension: str, *args):
    """
    Validates that the file has the provided extension
    Args
        extension (string): the expected extension
        *args: the file(s) to validate
    """
    log = logging.getLogger(__name__)

    for file in args:
        base, ext = os.path.splitext(file)
        if ext.lower() != extension.lower():
            error = 'Invalid extension: \'{0}\'. Provide a file with {1} extension'.format(file, extension)
            message = '{0}: {1}'.format('TypeError', error)
            log.error(message)
            raise TypeError(error)


def validate_paths_exist(*args):
    """
    Check if the files or directories exist in the system path
    Args
        *args: the files/directories to validate
    """
    log = logging.getLogger(__name__)

    for path in args:
        # Check if the provided path exists in the system path
        if not os.path.exists(path):
            error = FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
            message = '{0}: {1}'.format('FileNotFoundError', error)
            log.error(message)
            raise error
