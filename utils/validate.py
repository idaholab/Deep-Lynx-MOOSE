# Copyright 2021, Battelle Energy Alliance, LLC

import os
import errno
import logging
import configparser


def validateExtension(extension: str, *args):
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


def validatePathsExist(*args):
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


def validateChangesToInputFile(jsonData: list):
    """
    Validate the json objects before changing the input file that will be run in MOOSE
    Args
        jsonData (list): an array of json objects from Deep Lynx
    Return
        True: When all json objects are checked with a valid node, parameter, and datatype
        False: When a invalid node, parameter, or datatype was provided in a json object
    """

    # Read the config file
    config = configparser.ConfigParser()
    read_files = config.read(os.getenv('CONFIG_FILE_NAME'))
    if os.getenv("CONFIG_FILE_NAME") in read_files:
        configNodes = config.sections()

        # Check each json object for a valid node, parameter, and datatype of value
        for jsonObj in jsonData:
            isNodeFound = False
            for configNode in configNodes:
                configParams = dict(config.items(configNode))
                # If a valid node: either subsection nodes or root node
                if jsonObj['node'] == configNode or (jsonObj['node'] == None and configNode == 'root'):
                    isNodeFound = True
                    isParameterFound = False
                    for configParam, configValue in configParams.items():
                        # If a valid parameter
                        if configParam == jsonObj['parameter']:
                            isParameterFound = True
                            # If a valid datatype
                            if type(jsonObj['value']).__name__ == configValue:
                                break
                            # Not a valid datatype
                            else:
                                logging.error(
                                    'Invalid parameter datatype from Deep Lynx: the object with the node(%s) and the parameter(%s) provided a value with an incorrect datatype(%s). The %s requires that %s be of datatype(%s)',
                                    configNode, configParam,
                                    type(jsonObj['value']).__name__, os.getenv('INPUT_FILE_NAME'), configParam,
                                    configValue)
                                return False
                    # Not a valid parameter
                    if not isParameterFound:
                        logging.error(
                            'Invalid Parameter from Deep Lynx: the object with the node(%s) and the parameter(%s) cannot be modified because the parameter is not specified in the configuration file. Modify %s or incoming data accordingly',
                            jsonObj['node'], jsonObj['parameter'], os.getenv('INPUT_FILE_NAME'))
                        return False
                    # Is a valid parameter, do not check other configNodes
                    else:
                        break
            # Not a valid node
            if not isNodeFound:
                logging.error(
                    'Invalid Node from Deep Lynx: the object with the node(%s) cannot be modified because the node is not specified in the configuration file. Modify %s or incoming data accordingly',
                    jsonObj['node'], os.getenv('INPUT_FILE_NAME'))
                return False
    else:
        logging.error("Failed to read configuration file %s", os.getenv("CONFIG_FILE_NAME"))
        return False
    # All json objects were validated
    return True
