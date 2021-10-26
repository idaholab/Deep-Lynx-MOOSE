# Copyright 2021, Battelle Energy Alliance, LLC
import os
import sys
import logging
import argparse
import configparser

import pyhit
import moosetree
import utils


def getParserArguments():
    """
    Gets the arguments provided by the user via the command-line
    Return 
        args: the arguments provided by the user and parsed by the Argument Parser
    """
    # Create command-line interface
    parser = argparse.ArgumentParser(prefix_chars='-',
                                     description='Provide a MOOSE input file (.i) to generate a configuration file',
                                     add_help=False)
    options = parser.add_argument_group(title='Options')
    options.add_argument('-i', metavar='<input_file>', dest='inputFile', help='Specify a MOOSE input file', nargs=1)
    options.add_argument('-h', '--help', action='help', help='Displays CLI usage statement')
    args, unknown = parser.parse_known_args()
    # Validate the input file has ".i" extension
    utils.validateExtension(".i", args.inputFile[0])
    return args


def getInputFilePath(args):
    """
    Gets the path to the input file
    Return
        inputFile (string): the file path to the input file 
        isEnvVariable (bool): whether using the .env file or not (command-line)  
    """
    isEnvVariable = False
    # Determine the input file depending on the use of the command-line interface
    if args.inputFile is not None:
        inputFile = args.inputFile[0]
    else:
        from . import settings
        inputFile = os.getenv("INPUT_FILE_NAME")
        isEnvVariable = True
    return inputFile, isEnvVariable


def getConfigFileName(inputFile: str = None):
    """
    Returns the name of the config file
    Args
        inputFile (string): the path to use for the config filename (command-line only)
    Return
        configFile (string): the file path to the config file    
    """
    if inputFile:
        base, extension = os.path.splitext(inputFile)
        configFile = '.'.join([base, 'cfg'])
    else:
        configFile = os.getenv("CONFIG_FILE_NAME")
    return configFile


def getParamsOfNode(node: moosetree.Node, root: moosetree.Node):
    """
    Determine the parameters that can be modified which have a comment with '{{config}})'
    Args
        node (Node): a moosetree node
        root (Node): the root moosetree node
    Return
        section (string): the full path of the node
        paramDict (dictionary): dictionary of key, value pairs of the parameter name and the datatype
    """

    # Get the key, value for the parameters of this node
    nodeParameters = dict(node.params())
    if root:
        rootParameters = dict(root.params())
    paramsDict = dict()
    # Determine parameters with the comment {{config}} to add to the config file
    for nodeKey, nodeValue in nodeParameters.items():
        comment = node.comment(param=nodeKey)
        if comment is not None:
            if '{{config}}' in comment:
                if isinstance(nodeValue, str):
                    # If value is a global variable at top of input file, use the datatype of the parameter from configDict
                    # Purpose: type('${xmax}') = str but should be int
                    if '${' in nodeValue:
                        modifiedValue = nodeValue.replace('${', '')
                        modifiedValue = modifiedValue.replace('}', '')
                        for rootKey, rootValue in rootParameters.items():
                            if rootKey == modifiedValue:
                                paramsDict[nodeKey] = type(rootValue).__name__
                    else:
                        paramsDict[nodeKey] = type(nodeValue).__name__
                else:
                    paramsDict[nodeKey] = type(nodeValue).__name__

    # Return sections and a dictionary of parameters
    if len(paramsDict) != 0:
        if node.fullpath:
            section = node.fullpath
        else:
            section = 'root'
        return section, paramsDict


def getConfigParameters(inputFile: str):
    """
    Determine the section and parameters for the configuration file
    Args
        inputFile (string): the input file for pyhit to read
    Return
        configParams (dictionary): a dictionary of configuration parameters {section: dict(parameter name: datatype of value)}
    """

    configParams = dict()
    # Read the file
    root = pyhit.load(inputFile)
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))

    # For root node: Determine global variables with the comment {{config}} to add to the config file
    section, paramsDict = getParamsOfNode(root, None) or (None, None)
    if section and paramsDict:
        configParams[section] = paramsDict

    # For subsection nodes: Determine parameters with the comment {{config}} to add to the config file
    for node in nodes:
        section, paramsDict = getParamsOfNode(node, root) or (None, None)
        if section and paramsDict:
            configParams[section] = paramsDict
    return configParams


def writeConfigFile(configParams: dict, configFile: str):
    """
    Write the config parameters to a configuration file
    Args
        configParams (dictionary): a dictionary of configuration parameters {section: dict(parameter name: datatype of value)}
        configFile (string): name of the configuration file to write
    Return
        True: if config file path exists
        False: if config file path does not exist
    """

    config = configparser.ConfigParser()
    for key, value in configParams.items():
        config[key] = value
    # Write config to file
    with open(configFile, 'w') as configfile:
        config.write(configfile)
        if os.path.exists(configFile):
            return True
    return False


def main():
    """ Main entry point for script 
    Return
        True: if successfully generated a configuration file
        False: if invalid input file
    """
    args = getParserArguments()
    inputFile, isEnvVariable = getInputFilePath(args)
    utils.validatePathsExist(inputFile)
    if isEnvVariable:
        logging.info('Template Parser started. Using input file %s', os.getenv('INPUT_FILE_NAME'))
        configFile = getConfigFileName()
    else:
        configFile = getConfigFileName(inputFile)
    configParams = getConfigParameters(inputFile)
    isConfigFileCreated = writeConfigFile(configParams, configFile)
    if isConfigFileCreated:
        if isEnvVariable:
            logging.info(
                'Success: The Template Parser used the MOOSE input file %s to generate a configuration file %s',
                os.getenv('INPUT_FILE_NAME'), os.getenv('CONFIG_FILE_NAME'))
        else:
            print('Success: The provided MOOSE input file %s generated a configuration file %s' %
                  (inputFile, configFile))
        return True
    else:
        if isEnvVariable:
            logging.error('Fail: Provide a valid path to a MOOSE input file (.i) to generate a configuration file')
        else:
            print('Fail: Provide a valid path to a MOOSE input file (.i) to generate a configuration file')
        return False


if __name__ == '__main__':
    main()
