# Copyright 2021, Battelle Energy Alliance, LLC

import pytest
import os
import logging
import deep_lynx

import pyhit
import moosetree

from adapter import edit_input_file
from adapter import settings


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

    def test_valid_json_data(self):
        """
        Assert that a valid list of json objects was returned
        Test Case (createJSONData): Valid list of json objects that contain the correct information
            """
        jsonData = edit_input_file.createJSONData()
        for i in range(len(jsonData)):
            assert isinstance(jsonData, list) == True
            assert isinstance(jsonData[i], dict) == True
            node = jsonData[i].get('node', 'not exist')
            assert node != 'not exist'
            parameter = jsonData[i].get('parameter', 'not exist')
            assert parameter != 'not exist'
            value = jsonData[i].get('value', 'not exist')
            assert value != 'not exist'
            notExist = jsonData[i].get('city', 'not exist')
            assert notExist == 'not exist'

    def test_invalid_node(self):
        """
        Assert that an incorrect json object is provided 
        Test Case (validateChangesToInputFile): Invalid Deep Lynx json object because an invalid node is provided
        """
        jsonData = [{"node": "/B", "parameter": "year", "value": 2000}]
        isValidated = edit_input_file.validateChangesToInputFile(jsonData)
        assert isValidated == False

    def test_invalid_parameter(self):
        """
        Assert that an incorrect json object is provided 
        Test Case (validateChangesToInputFile): Invalid Deep Lynx json object because an invalid parameter is provided
        """
        jsonData = [{"node": "/A", "parameter": "decade", "value": 8}]
        isValidated = edit_input_file.validateChangesToInputFile(jsonData)
        assert isValidated == False

    def test_invalid_value(self):
        """
        Assert that an incorrect json object is provided 
        Test Case (validateChangesToInputFile): Invalid Deep Lynx json object because an invalid value is provided
        """
        jsonData = [{"node": "/A", "parameter": "year", "value": '2000'}]
        isValidated = edit_input_file.validateChangesToInputFile(jsonData)
        assert isValidated == False

    def test_valid_node_parameter_value(self):
        """
        Assert that a correct json object is provided 
        Test Case (validateChangesToInputFile): Valid Deep Lynx json object with a correct node, parameter, and  value
        """
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        isValidated = edit_input_file.validateChangesToInputFile(jsonData)
        assert isValidated == True

    def test_valid_update_parameter_value(self):
        """
        Assert that for a parameter of a node, the value was updated and a comment with {{change}} was added
        Test Case (updateParameterValues): The value of a parameter was updated
        """
        jsonObj = {"node": "/A", "parameter": "year", "value": 2000}
        # Read the file
        root = pyhit.load(os.path.abspath(self.CONFIG_INPUT_FILE_NAME))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        for node in nodes:
            edit_input_file.updateParameterValues(node, jsonObj)
            assert node['year'] == 2000
            comment = node.comment(param='year')
            assert comment.find('{{change}}') != -1

    def test_valid_remove_config_comments(self):
        """
        Assert that a comment with {{config}} was not found
        Test Case (removeConfigComments): No {{config}} in the comments
        """
        jsonObj = {"node": "/A", "parameter": "year", "value": 2000}
        # Read the file
        root = pyhit.load(os.path.abspath(self.CONFIG_INPUT_FILE_NAME))
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        for node in nodes:
            edit_input_file.updateParameterValues(node, jsonObj)
            edit_input_file.removeConfigComments(node)
            yearComment = node.comment(param='year')
            assert yearComment.find('{{config}}') == -1
            monthComment = node.comment(param='month')
            assert monthComment.find('{{config}}') == -1

    def test_valid_modify_input_file(self):
        """
        Assert that a input file was created
        Test Case (modifyInputFile): Input file is created
        """
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        edit_input_file.modifyInputFile(jsonData)
        assert os.path.isfile(self.RUN_FILE_NAME) == True
        if os.path.isfile(self.RUN_FILE_NAME):
            os.remove(self.RUN_FILE_NAME)
