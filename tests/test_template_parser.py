# Copyright 2021, Battelle Energy Alliance, LLC
import pytest
import argparse
import sys
import os

import pyhit
import moosetree

from adapter import template_parser
from adapter import settings

parser_path = os.path.join('adapter', 'template_parser.py')


def test_validInputFile_invalid():
    """Raise an ArgumentTypeError when the input file does not have a .i extension
        Test Case: file does not have .i extension"""
    with pytest.raises(argparse.ArgumentTypeError):
        template_parser.validInputFile('inputFile.txt')


def test_validInputFile_valid():
    """Assert that an input file has a .i extension
        Test Case: file has .i extension"""
    assert template_parser.validInputFile('inputFile.i') == 'inputFile.i'


def test_getParserArguments_exist():
    """Assert that an input file passed in via the command line is parsed accordingly
        Test Case: Using an input file provided through the console"""
    sys.argv = [parser_path, '-i', 'inputFile.i']
    args = template_parser.getParserArguments()
    assert args.inputFile[0] == 'inputFile.i'


def test_getParserArguments_none():
    """Assert that no arguments passed in via the command line is parsed accordingly
        Test Case: Using an input file provided through an env variable"""
    sys.argv = [parser_path]
    args = template_parser.getParserArguments()
    assert args.inputFile == None


def test_getInputFileName_env():
    """Assert that the input file is provided by the env variable
        Test Case: Using an input file provided through an env variable"""
    sys.argv = [parser_path]
    args = template_parser.getParserArguments()
    inputFile, isEnvVariable = template_parser.getInputFileName(args)
    assert isEnvVariable == True
    assert inputFile == os.getenv("INPUT_FILE_NAME")


def test_getInputFileName_console():
    """Assert that the input file is provided by the command line
        Test Case: Using an input file provided through the console"""
    sys.argv = [parser_path, '-i', 'inputFile.i']
    args = template_parser.getParserArguments()
    inputFile, isEnvVariable = template_parser.getInputFileName(args)
    assert isEnvVariable == False
    assert inputFile == 'inputFile.i'


def test_validateInputFileExists_exist():
    """Assert that the provided file exists
        Test Case: Check that an existing file in the repository is present"""
    assert template_parser.validateInputFileExists(parser_path) == True


def test_validateInputFileExists_notExist():
    """Assert that the provided file does not exist
        Test Case: Check that an non-existing file is not present"""
    assert template_parser.validateInputFileExists('xxxx.txt') == False


def test_getConfigFileName_envVariable():
    """Assert that the file extension is changed to .cfg
        Test Case: Check that a provided file is changed to have a file extension .cfg"""
    assert template_parser.getConfigFileName(True, 'inputFile.txt') == os.getenv('CONFIG_FILE_NAME')


def test_getConfigFileName_fileExtension():
    """Assert that the file extension is changed to .cfg
        Test Case: Check that a provided file is changed to have a file extension .cfg"""
    assert template_parser.getConfigFileName(False, 'inputFile.txt') == 'inputFile.cfg'


def test_getConfigFileName_noFileExtension():
    """Assert that the file extension .cfg was add to the name of the file
        Test Case: Check that a provided file name was given a file extension .cfg"""
    assert template_parser.getConfigFileName(False, 'inputFile') == 'inputFile.cfg'


def test_getParamsOfNode_scenario01():
    """Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case: A parameter equals a datatype int within a Node has a {{config}} comment
        Test Case: A parameter equals a datatype string within a Node has a {{config}} comment"""
    # Read the file
    root = pyhit.load(os.path.join('tests', 'test_input_files', 'test01.i'))
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
    section, paramsDict = template_parser.getParamsOfNode(nodes[0], root) or (None, None)
    expectedParamsDict = dict()
    expectedParamsDict['year'] = 'int'
    expectedParamsDict['month'] = 'str'
    expectedParamsDict['day'] = 'int'
    assert section == '/A'
    assert paramsDict == expectedParamsDict


def test_getParamsOfNode_scenario02():
    """Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case: A global variable within root has a {{config}} comment
        Test Case: A parameter equals global variable within a Node has a {{config}} comment"""
    # Read the file
    root = pyhit.load(os.path.join('tests', 'test_input_files', 'test02.i'))
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
    section, paramsDict = template_parser.getParamsOfNode(root, None) or (None, None)
    expectedParamsDict = dict()
    expectedParamsDict['month'] = 'int'
    assert section == 'root'
    assert paramsDict == expectedParamsDict
    section, paramsDict = template_parser.getParamsOfNode(nodes[0], root) or (None, None)
    expectedParamsDict = dict()
    expectedParamsDict['month'] = 'int'
    assert section == '/A'
    assert paramsDict == expectedParamsDict


def test_getParamsOfNode_scenario03():
    """Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case: A global variable within the root has a {{config}} comment
        Test Case: A node has no {{config}} comments"""
    # Read the file
    root = pyhit.load(os.path.join('tests', 'test_input_files', 'test03.i'))
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
    section, paramsDict = template_parser.getParamsOfNode(root, None) or (None, None)
    expectedParamsDict = dict()
    expectedParamsDict['month'] = 'int'
    assert section == 'root'
    assert paramsDict == expectedParamsDict
    section, paramsDict = template_parser.getParamsOfNode(nodes[0], root) or (None, None)
    assert section == None
    assert paramsDict == None


def test_getParamsOfNode_scenario04():
    """Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case: A parameter equals global variable within a Node has a {{config}} comment"""
    # Read the file
    root = pyhit.load(os.path.join('tests', 'test_input_files', 'test04.i'))
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
    section, paramsDict = template_parser.getParamsOfNode(nodes[0], root) or (None, None)
    expectedParamsDict = dict()
    expectedParamsDict['month'] = 'int'
    assert section == '/A'
    assert paramsDict == expectedParamsDict


def test_getConfigParameters_scenario01():
    """Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case: A parameter within a Node has a {{config}} comment"""
    configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_input_files', 'test01.i'))
    expectedConfigParams = dict()
    expectedConfigParams['/A'] = {'year': 'int', 'month': 'str', 'day': 'int'}
    assert configParams == expectedConfigParams


def test_getConfigParameters_scenario02():
    """Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case: A global variable within root has a {{config}} comment
        Test Case: A parameter equals global variable within a Node has a {{config}} comment"""
    configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_input_files', 'test02.i'))
    expectedConfigParams = dict()
    expectedConfigParams['root'] = {'month': 'int'}
    expectedConfigParams['/A'] = {'month': 'int'}
    assert configParams == expectedConfigParams


def test_getConfigParameters_scenario03():
    """Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case: A global variable within the root has a {{config}} comment
        Test Case: A node has no {{config}} comments"""
    configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_input_files', 'test03.i'))
    expectedConfigParams = dict()
    expectedConfigParams['root'] = {'month': 'int'}
    assert configParams == expectedConfigParams


def test_getConfigParameters_scenario04():
    """Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case: A parameter equals global variable within a Node has a {{config}} comment"""
    configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_input_files', 'test04.i'))
    expectedConfigParams = dict()
    expectedConfigParams['/A'] = {'month': 'int'}
    assert configParams == expectedConfigParams


def test_writeConfigFile_exist():
    """Assert that a dummy configuration file was created
        Test Case: Create a dummy configuration file"""
    configParams = dict()
    configParams['/A'] = {'year': 'int'}
    configFilePath = os.path.join('tests', 'test_input_files', 'test01.cfg')
    template_parser.writeConfigFile(configParams, configFilePath)
    assert os.path.isfile(configFilePath) == True
    if os.path.isfile(configFilePath):
        os.remove(configFilePath)


def test_main_console_success():
    """Assert that the Template Parser succeeded in creating a configuration file
        Test Case: Using the Template Parser with a valid input file via the command line"""
    inputFilePath = os.path.join('tests', 'test_input_files', 'test01.i')
    configFilePath = os.path.join('tests', 'test_input_files', 'test01.cfg')
    sys.argv = [parser_path, '-i', inputFilePath]
    didSucceed = template_parser.main()
    assert didSucceed == True
    assert os.path.isfile(configFilePath) == True
    if os.path.isfile(configFilePath):
        os.remove(configFilePath)


def test_main_console_fail():
    """Assert that the Template Parser failed in creating a configuration file
        Test Case: Using the Template Parser with an invalid input file via the command line"""
    inputFilePath = os.path.join('tests', 'test01.i')
    configFilePath = os.path.join('tests', 'test01.cfg')
    sys.argv = [parser_path, '-i', inputFilePath]
    didSucceed = template_parser.main()
    assert didSucceed == False
    assert os.path.isfile(configFilePath) == False
    if os.path.isfile(configFilePath):
        os.remove(configFilePath)


def test_main_env_success():
    """Assert that the Template Parser succeeded in creating a configuration file
        Test Case: Using the Template Parser using an env variable"""
    sys.argv = [parser_path]
    inputFilePath = os.path.join('tests', 'test_input_files', 'test01.i')
    configFilePath = os.path.join('tests', 'test_input_files', 'test01.cfg')
    os.environ['INPUT_FILE_NAME'] = inputFilePath
    os.environ['CONFIG_FILE_NAME'] = configFilePath
    didSucceed = template_parser.main()
    assert didSucceed == True
    assert os.path.isfile(configFilePath) == True
    if os.path.isfile(configFilePath):
        os.remove(configFilePath)


def test_main_env_fail():
    """Assert that the Template Parser failed in creating a configuration file
        Test Case: Using the Template Parser using an invalid env variable"""
    sys.argv = [parser_path]
    inputFilePath = os.path.join('tests', 'test01.i')
    configFilePath = os.path.join('tests', 'test01.cfg')
    os.environ['INPUT_FILE_NAME'] = inputFilePath
    didSucceed = template_parser.main()
    assert didSucceed == False
    assert os.path.isfile(configFilePath) == False
    if os.path.isfile(configFilePath):
        os.remove(configFilePath)
