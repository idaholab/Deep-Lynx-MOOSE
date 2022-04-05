# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import pytest
import sys
import os
import logging

# Repository Modules
from adapter import template_parser

# MOOSE Modules
import pyhit
import moosetree


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
    TEMPLATE_INPUT_FILE_NAME = os.path.join('tests', 'test_files', 'test01.i')
    CONFIG_FILE_NAME = os.path.join('tests', 'test_files', 'test01.cfg')
    RUN_FILE_NAME = os.path.join('tests', 'test_files', 'test01_run.i')
    IMPORT_FILE_NAME = os.path.join('data', 'example', 'import_file.csv')
    IMPORT_FILE_WAIT_SECONDS = 5
    REGISTER_WAIT_SECONDS = 5

    PARSER_PATH = os.path.join('adapter', 'template_parser.py')

    def test_valid_parsing_arguments(self):
        """
        Assert that an input file passed in via the command line is parsed accordingly
        Test Case (get_parser_arguments): Using an input file provided through the console
        """
        sys.argv = [self.PARSER_PATH, '-i', 'inputFile.i']
        args = template_parser.get_parser_arguments()
        assert args.input_file[0] == 'inputFile.i'

    def test_no_parsing_arguments(self):
        """
        Assert that no arguments passed in via the command line is parsed accordingly
        Test Case (get_parser_arguments): Using an input file provided through an env variable
        """
        sys.argv = [self.PARSER_PATH]
        args = template_parser.get_parser_arguments()
        assert args.input_file == None

    def test_valid_env_input_file_path(self):
        """
        Assert that the input file is provided by the env variable
        Test Case (get_input_file_path): Using an input file provided through an env variable
        """
        sys.argv = [self.PARSER_PATH]
        args = template_parser.get_parser_arguments()
        input_file, is_env_variable = template_parser.get_input_file_path(args)
        assert is_env_variable == True
        assert input_file == os.getenv("TEMPLATE_INPUT_FILE_NAME")

    def test_valid_console_input_file_path(self):
        """
        Assert that the input file is provided by the command line
        Test Case (get_input_file_path): Using an input file provided through the console
        """
        sys.argv = [self.PARSER_PATH, '-i', 'inputFile.i']
        args = template_parser.get_parser_arguments()
        input_file, is_env_variable = template_parser.get_input_file_path(args)
        assert is_env_variable == False
        assert input_file == 'inputFile.i'

    def test_valid_env_config_file_name(self):
        """
        Assert that the file extension is changed to .cfg
        Test Case (get_config_file_name): Check that a provided file is changed to the env configuration file name
        """
        assert template_parser.get_config_file_name() == os.getenv('CONFIG_FILE_NAME')

    def test_valid_console_config_file_name(self):
        """
        Assert that the file extension is changed to .cfg
        Test Case (get_config_file_name): Check that a provided file is changed to have a file extension .cfg for the console
        """
        assert template_parser.get_config_file_name('inputFile.txt') == 'inputFile.cfg'

    def test_valid_local_parameters_of_node(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (get_params_of_node): A parameter equals a datatype int within a Node has a {{config}} comment
        Test Case (get_params_of_node): A parameter equals a datatype string within a Node has a {{config}} comment
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test01.i'))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        section, params_dict = template_parser.get_params_of_node(nodes[0], root) or (None, None)
        expected_params_dict = dict()
        expected_params_dict['year'] = 'int'
        expected_params_dict['month'] = 'str'
        expected_params_dict['day'] = 'int'
        assert section == '/A'
        assert params_dict == expected_params_dict

    def test_valid_global_parameters_of_node_01(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (get_params_of_node): A global variable within root has a {{config}} comment
        Test Case (get_params_of_node): A parameter equals global variable within a Node has a {{config}} comment
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test02.i'))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        section, params_dict = template_parser.get_params_of_node(root, None) or (None, None)
        expected_params_dict = dict()
        expected_params_dict['month'] = 'int'
        assert section == 'root'
        assert params_dict == expected_params_dict
        section, params_dict = template_parser.get_params_of_node(nodes[0], root) or (None, None)
        expected_params_dict = dict()
        expected_params_dict['month'] = 'int'
        assert section == '/A'
        assert params_dict == expected_params_dict

    def test_valid_global_parameters_of_node_02(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (get_params_of_node): A global variable within the root has a {{config}} comment
        Test Case (get_params_of_node): A node has no {{config}} comments
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test03.i'))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        section, params_dict = template_parser.get_params_of_node(root, None) or (None, None)
        expected_params_dict = dict()
        expected_params_dict['month'] = 'int'
        assert section == 'root'
        assert params_dict == expected_params_dict
        section, params_dict = template_parser.get_params_of_node(nodes[0], root) or (None, None)
        assert section == None
        assert params_dict == None

    def test_valid_global_parameters_of_node_03(self):
        """
        Assert that the expected section and dictionary of parameters {parameter name: datatype of parameter value} are returned
        Test Case (get_params_of_node): A parameter equals global variable within a Node has a {{config}} comment
        """
        # Read the file
        root = pyhit.load(os.path.join('tests', 'test_files', 'test04.i'))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        section, params_dict = template_parser.get_params_of_node(nodes[0], root) or (None, None)
        expected_params_dict = dict()
        expected_params_dict['month'] = 'int'
        assert section == '/A'
        assert params_dict == expected_params_dict

    def test_valid_local_config_parameters(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (get_config_parameters): A parameter within a Node has a {{config}} comment
        """
        config_params = template_parser.get_config_parameters(os.path.join('tests', 'test_files', 'test01.i'))
        expected_config_params = dict()
        expected_config_params['/A'] = {'year': 'int', 'month': 'str', 'day': 'int'}
        assert config_params == expected_config_params

    def test_valid_global_config_parameters_01(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (get_config_parameters): A global variable within root has a {{config}} comment
        Test Case (get_config_parameters): A parameter equals global variable within a Node has a {{config}} comment
        """
        config_params = template_parser.get_config_parameters(os.path.join('tests', 'test_files', 'test02.i'))
        expected_config_params = dict()
        expected_config_params['root'] = {'month': 'int'}
        expected_config_params['/A'] = {'month': 'int'}
        assert config_params == expected_config_params

    def test_valid_global_config_parameters_02(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (get_config_parameters): A global variable within the root has a {{config}} comment
        Test Case (get_config_parameters): A node has no {{config}} comments
        """
        config_params = template_parser.get_config_parameters(os.path.join('tests', 'test_files', 'test03.i'))
        expected_config_params = dict()
        expected_config_params['root'] = {'month': 'int'}
        assert config_params == expected_config_params

    def test_valid_global_config_parameters_03(self):
        """
        Assert that the expected configuration dictionary { section: {parameter name: datatype of parameter value}} is returned
        Test Case (get_config_parameters): A parameter equals global variable within a Node has a {{config}} comment
        """
        config_params = template_parser.get_config_parameters(os.path.join('tests', 'test_files', 'test04.i'))
        expected_config_params = dict()
        expected_config_params['/A'] = {'month': 'int'}
        assert config_params == expected_config_params

    def test_valid_write_config_file(self):
        """
        Assert that a dummy configuration file was created
        Test Case (write_config_file): Create a dummy configuration file
        """
        config_params = dict()
        config_params['/A'] = {'year': 'int'}
        configFilePath = os.path.join('tests', 'test_files', 'test01.cfg')
        template_parser.write_config_file(config_params, configFilePath)
        assert os.path.isfile(configFilePath) == True
