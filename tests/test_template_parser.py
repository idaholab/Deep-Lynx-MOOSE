# Copyright 2021, Battelle Energy Alliance, LLC

import pytest
import sys
import os
import logging

import pyhit
import moosetree

from adapter import template_parser


class TestEditInputFile:

    dl_service = None
    log_path = 'test.log'
    # Setup logging
    # Remove log file if it exists
    if os.path.exists(log_path):
        os.remove(log_path)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=log_path, level=logging.INFO)
    logger = logging.getLogger('moose-adapter')

    # Environment Variables
    DEEP_LYNX_URL = os.getenv("DEEP_LYNX_URL")
    CONTAINER_NAME = os.getenv("CONTAINER_NAME")
    DATA_SOURCE_NAME = os.getenv("DATA_SOURCE_NAME")
    PYTHONPATH = os.path.join('~', 'projects', 'moose', 'python')
    MOOSE_OPT_PATH = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
    QUERY_FILE_NAME = os.path.join('data', 'example', 'query_file.csv')
    CONFIG_INPUT_FILE_NAME = os.path.join('tests', 'test_files', 'test01.i')
    CONFIG_FILE_NAME = os.path.join('tests', 'test_files', 'test01.cfg')
    RUN_FILE_NAME = os.path.join('tests', 'test_files', 'test01_run.i')
    IMPORT_FILE_NAME = os.path.join('data', 'example', 'import_file.csv')
    QUERY_FILE_WAIT_SECONDS = 5
    IMPORT_FILE_WAIT_SECONDS = 5
    REGISTER_WAIT_SECONDS = 5

    PARSER_PATH = os.path.join('adapter', 'template_parser.py')

    def test_valid_parsing_arguments(self):
        """
        Assert that an input file passed in via the command line is parsed accordingly
        Test Case (getParserArguments): Using an input file provided through the console
        """
        sys.argv = [self.PARSER_PATH, '-i', 'inputFile.i']
        args = template_parser.getParserArguments()
        assert args.inputFile[0] == 'inputFile.i'

    def test_no_parsing_arguments(self):
        """
        Assert that no arguments passed in via the command line is parsed accordingly
        Test Case (getParserArguments): Using an input file provided through an env variable
        """
        sys.argv = [self.PARSER_PATH]
        args = template_parser.getParserArguments()
        assert args.inputFile == None

    def test_valid_env_input_file_path(self):
        """
        Assert that the input file is provided by the env variable
        Test Case (getInputFilePath): Using an input file provided through an env variable
        """
        sys.argv = [self.PARSER_PATH]
        args = template_parser.getParserArguments()
        inputFile, isEnvVariable = template_parser.getInputFilePath(args)
        assert isEnvVariable == True
        assert inputFile == os.getenv("CONFIG_INPUT_FILE_NAME")

    def test_valid_console_input_file_path(self):
        """
        Assert that the input file is provided by the command line
        Test Case (getInputFilePath): Using an input file provided through the console
        """
        sys.argv = [self.PARSER_PATH, '-i', 'inputFile.i']
        args = template_parser.getParserArguments()
        inputFile, isEnvVariable = template_parser.getInputFilePath(args)
        assert isEnvVariable == False
        assert inputFile == 'inputFile.i'

    def test_valid_env_config_file_name(self):
        """
        Assert that the file extension is changed to .cfg
        Test Case (getConfigFileName): Check that a provided file is changed to the env configuration file name
        """
        assert template_parser.getConfigFileName() == os.getenv('CONFIG_FILE_NAME')

    def test_valid_console_config_file_name(self):
        """
        Assert that the file extension is changed to .cfg
        Test Case (getConfigFileName): Check that a provided file is changed to have a file extension .cfg for the console
        """
        assert template_parser.getConfigFileName('inputFile.txt') == 'inputFile.cfg'

    def test_valid_local_parameters_of_node(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (getParamsOfNode): A parameter equals a datatype int within a Node has a {{config}} comment
        Test Case (getParamsOfNode): A parameter equals a datatype string within a Node has a {{config}} comment
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test01.i'))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        section, paramsDict = template_parser.getParamsOfNode(nodes[0], root) or (None, None)
        expectedParamsDict = dict()
        expectedParamsDict['year'] = 'int'
        expectedParamsDict['month'] = 'str'
        expectedParamsDict['day'] = 'int'
        assert section == '/A'
        assert paramsDict == expectedParamsDict

    def test_valid_global_parameters_of_node_01(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (getParamsOfNode): A global variable within root has a {{config}} comment
        Test Case (getParamsOfNode): A parameter equals global variable within a Node has a {{config}} comment
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test02.i'))
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

    def test_valid_global_parameters_of_node_02(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (getParamsOfNode): A global variable within the root has a {{config}} comment
        Test Case (getParamsOfNode): A node has no {{config}} comments
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test03.i'))
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

    def test_valid_global_parameters_of_node_03(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (getParamsOfNode): A parameter equals global variable within a Node has a {{config}} comment
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test04.i'))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        section, paramsDict = template_parser.getParamsOfNode(nodes[0], root) or (None, None)
        expectedParamsDict = dict()
        expectedParamsDict['month'] = 'int'
        assert section == '/A'
        assert paramsDict == expectedParamsDict

    def test_valid_local_config_parameters(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (getConfigParameters): A parameter within a Node has a {{config}} comment
        """
        configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_files', 'test01.i'))
        expectedConfigParams = dict()
        expectedConfigParams['/A'] = {'year': 'int', 'month': 'str', 'day': 'int'}
        assert configParams == expectedConfigParams

    def test_valid_global_config_parameters_01(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (getConfigParameters): A global variable within root has a {{config}} comment
        Test Case (getConfigParameters): A parameter equals global variable within a Node has a {{config}} comment
        """
        configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_files', 'test02.i'))
        expectedConfigParams = dict()
        expectedConfigParams['root'] = {'month': 'int'}
        expectedConfigParams['/A'] = {'month': 'int'}
        assert configParams == expectedConfigParams

    def test_valid_global_config_parameters_02(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (getConfigParameters): A global variable within the root has a {{config}} comment
        Test Case (getConfigParameters): A node has no {{config}} comments
        """
        configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_files', 'test03.i'))
        expectedConfigParams = dict()
        expectedConfigParams['root'] = {'month': 'int'}
        assert configParams == expectedConfigParams

    def test_valid_global_config_parameters_03(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (getConfigParameters): A parameter equals global variable within a Node has a {{config}} comment
        """
        configParams = template_parser.getConfigParameters(os.path.join('tests', 'test_files', 'test04.i'))
        expectedConfigParams = dict()
        expectedConfigParams['/A'] = {'month': 'int'}
        assert configParams == expectedConfigParams

    def test_valid_write_config_file(self):
        """
        Assert that a dummy configuration file was created
        Test Case (writeConfigFile): Create a dummy configuration file
        """
        configParams = dict()
        configParams['/A'] = {'year': 'int'}
        configFilePath = os.path.join('tests', 'test_files', 'test01.cfg')
        template_parser.writeConfigFile(configParams, configFilePath)
        assert os.path.isfile(configFilePath) == True
