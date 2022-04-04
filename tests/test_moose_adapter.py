# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import pytest
import os
import logging

# Repository Modules
from adapter import moose_adapter
import settings


class TestMOOSEAdapter:

    dl_service = None
    log_path = 'test.log'
    # Setup logging
    # Remove log file if it exists
    if os.path.exists(log_path):
        os.remove(log_path)

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=log_path, level=logging.INFO)
    logger = logging.getLogger('moose-adapter')

    DEEP_LYNX_URL = os.getenv("DEEP_LYNX_URL")
    CONTAINER_NAME = os.getenv("CONTAINER_NAME")
    DATA_SOURCE_NAME = os.getenv("DATA_SOURCE_NAME")
    PYTHONPATH = os.path.join('~', 'projects', 'moose', 'python')
    MOOSE_OPT_PATH = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
    QUERY_FILE_NAME = os.path.join('data', 'example', 'query_file.csv')
    CONFIG_INPUT_FILE_NAME = os.path.join('data', 'example', 'config_input_file.i')
    CONFIG_FILE_NAME = os.path.join('data', 'example', 'config_file.cfg')
    RUN_FILE_NAME = os.path.join('data', 'example', 'run_file.i')
    IMPORT_FILE_NAME = os.path.join('data', 'example', 'import_file.csv')
    IMPORT_FILE_WAIT_SECONDS = 1
    REGISTER_WAIT_SECONDS = 1

    def test_valid_query_deep_lynx(self):
        """
        Validate that the query file is found
        Test Case (queryDeepLynx): query file exists and is found
        """
        os.environ['QUERY_FILE_NAME'] = self.QUERY_FILE_NAME
        is_found = moose_adapter.queryDeepLynx()
        assert is_found == True

    def test_invalid_query_deep_lynx(self):
        """
        Validate that the query file is not found
        Test Case (queryDeepLynx): query file does not exist and is not found
        """
        # Invalid path to query file
        os.environ['QUERY_FILE_NAME'] = os.path.join('data', 'query_file.csv')
        is_found = moose_adapter.queryDeepLynx()
        assert is_found == False

    def test_valid_run_input_file(self):
        """
        Validate that the input file is successfully run in MOOSE
        Test Case (run_input_file): Successful run in MOOSE
        """
        os.environ['RUN_FILE_NAME'] = self.RUN_FILE_NAME
        is_run = moose_adapter.run_input_file()
        assert is_run == True

    def test_invalid_run_input_file(self):
        """
        Validate that the input file is run in MOOSE
        Test Case (run_input_file): Failed run in MOOSE
        """
        # Invalid moose executable path
        os.environ['MOOSE_OPT_PATH'] = os.path.join('~', 'projects', 'moose', 'moose_test-opt')
        with pytest.raises(FileNotFoundError):
            moose_adapter.run_input_file()

    def test_valid_import_to_deep_lynx(self):
        """
        Validate that the import file is found
        Test Case (importToDeepLynx): imort file exists and is found
        """
        os.environ['IMPORT_FILE_NAME'] = self.IMPORT_FILE_NAME
        is_found = moose_adapter.importToDeepLynx()
        assert is_found == True

    def test_invalid_import_to_deep_lynx(self):
        """
        Validate that the import file is not found
        Test Case (importToDeepLynx): import file does not exist and is not found
        """
        # Invalid path to query file
        os.environ['IMPORT_FILE_NAME'] = os.path.join('data', 'import_file.csv')
        os.environ['IMPORT_FILE_WAIT_SECONDS'] = "1"
        is_found = moose_adapter.importToDeepLynx()
        assert is_found == False
