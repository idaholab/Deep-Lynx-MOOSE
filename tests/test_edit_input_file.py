# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import pytest
import os
import logging

# Repository Modules
from adapter import edit_input_file

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

    def test_valid_json_data(self):
        """
        Assert that a valid list of json objects was returned
        Test Case (create_json_data): Valid list of json objects that contain the correct information
            """
        json_data = edit_input_file.create_json_data()
        for i in range(len(json_data)):
            assert isinstance(json_data, list) == True
            assert isinstance(json_data[i], dict) == True
            node = json_data[i].get('node', 'not exist')
            assert node != 'not exist'
            parameter = json_data[i].get('parameter', 'not exist')
            assert parameter != 'not exist'
            value = json_data[i].get('value', 'not exist')
            assert value != 'not exist'
            not_exist = json_data[i].get('city', 'not exist')
            assert not_exist == 'not exist'

    def test_invalid_node(self):
        """
        Assert that an incorrect json object is provided 
        Test Case (validate_changes_to_input_file): Invalid Deep Lynx json object because an invalid node is provided
        """
        json_data = [{"node": "/B", "parameter": "year", "value": 2000}]
        is_validated = edit_input_file.validate_changes_to_input_file(json_data)
        assert is_validated == False

    def test_invalid_parameter(self):
        """
        Assert that an incorrect json object is provided 
        Test Case (validate_changes_to_input_file): Invalid Deep Lynx json object because an invalid parameter is provided
        """
        json_data = [{"node": "/A", "parameter": "decade", "value": 8}]
        is_validated = edit_input_file.validate_changes_to_input_file(json_data)
        assert is_validated == False

    def test_invalid_value(self):
        """
        Assert that an incorrect json object is provided 
        Test Case (validate_changes_to_input_file): Invalid Deep Lynx json object because an invalid value is provided
        """
        json_data = [{"node": "/A", "parameter": "year", "value": '2000'}]
        is_validated = edit_input_file.validate_changes_to_input_file(json_data)
        assert is_validated == False

    def test_valid_node_parameter_value(self):
        """
        Assert that a correct json object is provided 
        Test Case (validate_changes_to_input_file): Valid Deep Lynx json object with a correct node, parameter, and  value
        """
        json_data = [{"node": "/A", "parameter": "year", "value": 2000}]
        os.environ['CONFIG_FILE_NAME'] = self.CONFIG_FILE_NAME
        is_validated = edit_input_file.validate_changes_to_input_file(json_data)
        assert is_validated == True

    def test_valid_update_parameter_value(self):
        """
        Assert that for a parameter of a node, the value was updated and a comment with {{change}} was added
        Test Case (update_parameter_values): The value of a parameter was updated
        """
        json_object = {"node": "/A", "parameter": "year", "value": 2000}
        # Read the file
        root = pyhit.load(os.path.abspath(self.TEMPLATE_INPUT_FILE_NAME))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        for node in nodes:
            edit_input_file.update_parameter_values(node, json_object)
            assert node['year'] == 2000
            comment = node.comment(param='year')
            assert comment.find('{{change}}') != -1

    def test_valid_remove_config_comments(self):
        """
        Assert that a comment with {{config}} was not found
        Test Case (remove_config_comments): No {{config}} in the comments
        """
        json_object = {"node": "/A", "parameter": "year", "value": 2000}
        # Read the file
        root = pyhit.load(os.path.abspath(self.TEMPLATE_INPUT_FILE_NAME))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        for node in nodes:
            edit_input_file.update_parameter_values(node, json_object)
            edit_input_file.remove_config_comments(node)
            year_comment = node.comment(param='year')
            assert year_comment.find('{{config}}') == -1
            month_comment = node.comment(param='month')
            assert month_comment.find('{{config}}') == -1

    def test_valid_modify_input_file(self):
        """
        Assert that a input file was created
        Test Case (modify_input_file): Input file is created
        """
        json_data = [{"node": "/A", "parameter": "year", "value": 2000}]
        os.environ['TEMPLATE_INPUT_FILE_NAME'] = self.TEMPLATE_INPUT_FILE_NAME
        os.environ['RUN_FILE_NAME'] = self.RUN_FILE_NAME
        edit_input_file.modify_input_file(json_data)
        assert os.path.isfile(self.RUN_FILE_NAME) == True
        if os.path.isfile(self.RUN_FILE_NAME):
            os.remove(self.RUN_FILE_NAME)
