# Copyright 2021, Battelle Energy Alliance, LLC

import pytest
import sys
import os
import logging
import deep_lynx

import pyhit
import moosetree

from adapter import moose_adapter
from adapter import template_parser
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

    # Deep Lynx environment variables
    DEEP_LYNX_URL = None
    CONTAINER_NAME = None
    DATA_SOURCE_NAME = None
    PYTHONPATH = None
    MOOSE_OPT_PATH = None
    QUERY_FILE_NAME = None
    CONFIG_INPUT_FILE_NAME = None
    CONFIG_FILE_NAME = None
    RUN_FILE_NAME = None
    IMPORT_FILE_NAME = None
    IMPORT_FILE_WAIT_SECONDS = None
    REGISTER_WAIT_SECONDS = None

    def set_env_success(self):
        """
        Setup for env variables
        Test Case: Correct env variables
        """
        DEEP_LYNX_URL = os.getenv("DEEP_LYNX_URL")
        CONTAINER_NAME = os.getenv("CONTAINER_NAME")
        DATA_SOURCE_NAME = os.getenv("DATA_SOURCE_NAME")
        PYTHONPATH = os.path.join('~', 'projects', 'moose', 'python')
        MOOSE_OPT_PATH = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
        QUERY_FILE_NAME = os.path.join('data', 'example', 'query_file.csv')
        CONFIG_INPUT_FILE_NAME = os.path.join('tests', 'test_files', 'test01.i')
        CONFIG_FILE_NAME = os.path.join('tests', 'test_files', 'test01.cfg')
        RUN_FILE_NAME = os.path.join('tests', 'test_files', 'test01_run.cfg')
        IMPORT_FILE_NAME = os.path.join('data', 'example', 'import_file.csv')
        QUERY_FILE_WAIT_SECONDS = 5
        IMPORT_FILE_WAIT_SECONDS = 5
        REGISTER_WAIT_SECONDS = 5

    @classmethod
    def setup_class(cls):
        """ 
        Setup any state specific to the execution of the given class
        """
        cls.logger.info('Setting up TestEditInputFile class')
        cls.set_env_success(cls)
        cls.dl_service = deep_lynx.DeepLynxService(cls.DEEP_LYNX_URL, cls.CONTAINER_NAME, cls.DATA_SOURCE_NAME)
        # create a test container
        if cls.dl_service.check_container() == False:
            cls.dl_service.create_container({'name': cls.CONTAINER_NAME, 'description': 'Test container'})

        # create a data source
        cls.dl_service.init()

        resp = cls.dl_service.import_container({
            'file_path': os.path.join('tests', 'test_files', 'test.owl'),
            'name': 'Test_Import_Container',
            'description': 'Description for my test container',
            'data_versioning_enabled': 'false'
        })
        if resp['isError']:
            cls.logger.error(resp)
        cls.container_id = resp['value']

    @classmethod
    def teardown_class(cls):
        """
        Teardown any state that was previously setup with a call to setup_class.
        """
        cls.logger.info('Tearing down TestEditInputFile class')
        cls.set_env_success(cls)
        if cls.dl_service.check_container() == True:
            # Delete datasource
            cls.dl_service.delete_data_source(cls.dl_service.container_id, cls.dl_service.data_source_id,
                                              {'forceDelete': 'true'})
            # Delete container
            resp = cls.dl_service.delete_container(cls.dl_service.container_id)
        if cls.container_id:
            resp = cls.dl_service.delete_container(cls.container_id)

    def test_createJSONData_exist():
        """Assert that a valid list of json objects was returned
            Test Case: Valid list of json objects that contain the correct information"""
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


    def test_validateChangesToInputFile_invalidNode():
        """Assert that an incorrect json object is provided 
            Test Case: Invalid Deep Lynx json object because an invalid node is provided"""
        jsonData = [{"node": "/B", "parameter": "year", "value": 2000}]
        createConfigFile_scenario01()
        isValidated = moose_adapter.validateDataToChangeInInputFile(jsonData)
        assert isValidated == False
        deleteConfigFile()


    def test_validateDataToChangeInInputFile_invalidParameter():
        """Assert that an incorrect json object is provided 
            Test Case: Invalid Deep Lynx json object because an invalid parameter is provided"""
        jsonData = [{"node": "/A", "parameter": "decade", "value": 8}]
        createConfigFile_scenario01()
        isValidated = moose_adapter.validateDataToChangeInInputFile(jsonData)
        assert isValidated == False
        deleteConfigFile()


    def test_validateDataToChangeInInputFile_invalidValue():
        """Assert that an incorrect json object is provided 
            Test Case: Invalid Deep Lynx json object because an invalid value is provided"""
        jsonData = [{"node": "/A", "parameter": "year", "value": '2000'}]
        createConfigFile_scenario01()
        isValidated = moose_adapter.validateDataToChangeInInputFile(jsonData)
        assert isValidated == False
        deleteConfigFile()


    def test_validateDataToChangeInInputFile_validJSON():
        """Assert that a correct json object is provided 
            Test Case: "Valid Deep Lynx json object with a correct node, parameter, and  value"""
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        createConfigFile_scenario01()
        isValidated = moose_adapter.validateDataToChangeInInputFile(jsonData)
        assert isValidated == True
        deleteConfigFile()


    def test_updateParameterValues():
        """Assert that for a parameter of a node, the value was updated and a comment with {{change}} was added
            Test Case: The value of a parameter was updated"""
        jsonObj = {"node": "/A", "parameter": "year", "value": 2000}
        createConfigFile_scenario01()
        # Read the file
        root = pyhit.load(inputFilePath)
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        for node in nodes:
            moose_adapter.updateParameterValues(node, jsonObj)
            assert node['year'] == 2000
            comment = node.comment(param='year')
            assert comment.find('{{change}}') != -1
        deleteConfigFile()


    def test_removeConfigComments():
        """Assert that a comment with {{config}} was not found
            Test Case: No {{config}} in the comments"""
        jsonObj = {"node": "/A", "parameter": "year", "value": 2000}
        createConfigFile_scenario01()
        # Read the file
        root = pyhit.load(inputFilePath)
        # Get nodes
        nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))
        for node in nodes:
            moose_adapter.updateParameterValues(node, jsonObj)
            moose_adapter.removeConfigComments(node)
            yearComment = node.comment(param='year')
            assert yearComment.find('{{config}}') == -1
            monthComment = node.comment(param='month')
            assert monthComment.find('{{config}}') == -1
        deleteConfigFile()


    def test_createInputFileToRun():
        """Assert that a input file was created
            Test Case: Input file is created"""
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        createConfigFile_scenario01()
        moose_adapter.createInputFileToRun(jsonData)
        assert os.path.isfile(runFilePath) == True
        deleteConfigFile()
