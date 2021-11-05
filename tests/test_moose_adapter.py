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
from adapter import settings


class TestMOOSEAdapter:

    dl_service = None
    log_path = 'test.log'
    # Setup logging
    # Remove log file if it exists
    if os.path.exists(log_path):
        os.remove(log_path)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=log_path, level=logging.INFO)
    logger = logging.getLogger('moose-adapter')

    # Deep Lynx environment variables
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
        RUN_FILE_NAME = os.path.join('tests', 'test_files', 'test01_run.i')
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
        if os.path.exists(os.path.join('tests', 'test_files', 'test01.cfg')):
            os.remove(os.path.join('tests', 'test_files', 'test01.cfg'))
        if os.path.exists(os.path.join('tests', 'test_files', 'test01_run.i')):
            os.remove(os.path.join('tests', 'test_files', 'test01_run.i'))

    inputFilePath = os.path.join('tests', 'test_input_files', 'test01.i')
    configFilePath = os.path.join('tests', 'test_input_files', 'test01.cfg')
    runFilePath = os.path.join('tests', 'test_input_files', 'test01_run.i')
    moose_executable = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
    moose_python = os.path.join('~', 'projects', 'moose', 'python')


    def createConfigFile_scenario01():
        sys.argv = [os.path.join('adapter', 'template_parser.py')]
        os.environ['CONFIG_INPUT_FILE_NAME'] = inputFilePath
        os.environ['CONFIG_FILE_NAME'] = configFilePath
        os.environ['RUN_FILE_NAME'] = runFilePath
        didSucceed = template_parser.main()


    def deleteConfigFile():
        if os.path.isfile(configFilePath):
            os.remove(configFilePath)
        if os.path.isfile(runFilePath):
            os.remove(runFilePath)


    def createConfigFile_scenario02_success():
        os.environ['CONFIG_INPUT_FILE_NAME'] = "data/input_file.i"
        os.environ['CONFIG_FILE_NAME'] = "data/config_file.cfg"
        os.environ['RUN_FILE_NAME'] = "data/run_file.i"
        os.environ['MOOSE_OPT_PATH'] = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
        didSucceed = template_parser.main()


    def createConfigFile_scenario02_fail():
        sys.argv = [os.path.join('adapter', 'template_parser.py')]
        os.environ['CONFIG_INPUT_FILE_NAME'] = inputFilePath
        os.environ['CONFIG_FILE_NAME'] = configFilePath
        os.environ['RUN_FILE_NAME'] = runFilePath
        os.environ['MOOSE_OPT_PATH'] = os.path.join('~', 'projects', 'moose', 'moose_test-opt')
        didSucceed = template_parser.main()


    def createConfigFile_scenario03():
        sys.argv = [os.path.join('adapter', 'template_parser.py')]
        os.environ['CONFIG_INPUT_FILE_NAME'] = os.getenv("CONFIG_INPUT_FILE_NAME")
        os.environ['CONFIG_FILE_NAME'] = os.getenv("CONFIG_FILE_NAME")
        os.environ['RUN_FILE_NAME'] = os.getenv("RUN_FILE_NAME")
        os.environ['IMPORT_FILE_NAME'] = os.getenv("IMPORT_FILE_NAME")
        os.environ['IMPORT_FILE_WAIT_SECONDS'] = '2'
        os.environ['PYTHONPATH'] = moose_python
        os.environ['MOOSE_OPT_PATH'] = moose_executable
        os.environ['DEEP_LYNX_URL'] = 'http://127.0.0.1:8090'
        os.environ['CONTAINER_NAME'] = 'DIAMOND'
        os.environ['DATA_SOURCE_NAME'] = 'MOOSEAdapter'
        didSucceed = template_parser.main()




    def test_validatePathsExist_valid():
        """Validate that MOOSE_OPT_PATH and RUN_FILE_NAME paths exist
            Test Case: Valid MOOSE_OPT_PATH and RUN_FILE_NAME paths"""
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        createConfigFile_scenario01()
        moose_adapter.createInputFileToRun(jsonData)
        os.environ['MOOSE_OPT_PATH'] = moose_executable
        os.environ['RUN_FILE_NAME'] = runFilePath
        isValidated = moose_adapter.validatePathsExist()
        assert isValidated == True
        deleteConfigFile()


    def test_validatePathsExist_invalidMooseOptPath():
        """Validate that MOOSE_OPT_PATH path does not exist
            Test Case: Invalid MOOSE_OPT_PATH path"""
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        createConfigFile_scenario01()
        moose_adapter.createInputFileToRun(jsonData)
        os.environ['MOOSE_OPT_PATH'] = os.path.join('~', 'projects', 'moose', 'moose_test-opt')
        os.environ['RUN_FILE_NAME'] = runFilePath
        isValidated = moose_adapter.validatePathsExist()
        assert isValidated == False
        deleteConfigFile()


    def test_validatePathsExist_invalidRunFileName():
        """Validate that RUN_FILE_NAME path does not exist
            Test Case: Invalid RUN_FILE_NAME path"""
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
        createConfigFile_scenario01()
        moose_adapter.createInputFileToRun(jsonData)
        os.environ['MOOSE_OPT_PATH'] = moose_executable
        os.environ['RUN_FILE_NAME'] = os.path.join('tests', 'x', 'test01_run.i')
        isValidated = moose_adapter.validatePathsExist()
        assert isValidated == False
        deleteConfigFile()


    def test_runInputFile_success():
        """Validate that the input file is run in MOOSE
            Test Case: Successful run in MOOSE"""
        createConfigFile_scenario02_success()
        jsonData = moose_adapter.createJSONData()
        moose_adapter.createInputFileToRun(jsonData)
        isRun = moose_adapter.runInputFile()
        assert isRun == True


    def test_runInputFile_fail():
        """Validate that the input file is run in MOOSE
            Test Case: Failed run in MOOSE"""
        createConfigFile_scenario02_fail()
        jsonData = moose_adapter.createJSONData()
        moose_adapter.createInputFileToRun(jsonData)
        isRun = moose_adapter.runInputFile()
        assert isRun == False
        deleteConfigFile()


    def test_getOutputFile_notExist():
        """Validate output file does not exist
            Test Case: Failed run in MOOSE"""
        createConfigFile_scenario03()
        jsonData = moose_adapter.createJSONData()
        moose_adapter.createInputFileToRun(jsonData)
        if os.path.isfile(os.getenv("IMPORT_FILE_NAME")):
            os.remove(os.getenv("IMPORT_FILE_NAME"))
        isOutputFile = moose_adapter.getOutputFile()
        assert isOutputFile == False
        deleteConfigFile()

