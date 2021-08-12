# Copyright 2021, Battelle Energy Alliance, LLC
import pytest
import sys
import os

import pyhit
import moosetree

from adapter import moose_adapter
from adapter import template_parser
from adapter import settings

inputFilePath = os.path.join('tests', 'test_input_files', 'test01.i')
configFilePath = os.path.join('tests', 'test_input_files', 'test01.cfg')
runFilePath = os.path.join('tests', 'test_input_files', 'test01_run.i')
moose_executable = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
moose_python = os.path.join('~', 'projects', 'moose', 'python')

event = {
    "creationDate": "2021-01-20T18:43:20.822Z",
    "creationUser": "default",
    "dataSourceID": "20aaa411-52ee-4317-b04b-c2a6ab268677",
    "id": "c779eae1-a034-46fd-8a8e-c2e1f816016e",
    "importID": "364cfe14-6ff4-49d0-a3ff-1c43d6e7eb3d",
    "instruction": "run",
    "metatypeName": "MultiphysicsDataItem",
    "modifiedDate": "2021-01-20T11:44:59.989554",
    "modifiedUser": "MOOSEAdapter",
    "originalDataID": "multiphysics data item id",
    "received": True,
    "status": "in progress"
}


def createConfigFile_scenario01():
    sys.argv = [os.path.join('adapter', 'template_parser.py')]
    os.environ['INPUT_FILE_NAME'] = inputFilePath
    os.environ['CONFIG_FILE_NAME'] = configFilePath
    os.environ['RUN_FILE_NAME'] = runFilePath
    didSucceed = template_parser.main()


def deleteConfigFile():
    if os.path.isfile(configFilePath):
        os.remove(configFilePath)
    if os.path.isfile(runFilePath):
        os.remove(runFilePath)


def createConfigFile_scenario02_success():
    os.environ['INPUT_FILE_NAME'] = "data/input_file.i"
    os.environ['CONFIG_FILE_NAME'] = "data/config_file.cfg"
    os.environ['RUN_FILE_NAME'] = "data/run_file.i"
    os.environ['MOOSE_OPT_PATH'] = os.path.join('~', 'projects', 'moose', 'test', 'moose_test-opt')
    didSucceed = template_parser.main()


def createConfigFile_scenario02_fail():
    sys.argv = [os.path.join('adapter', 'template_parser.py')]
    os.environ['INPUT_FILE_NAME'] = inputFilePath
    os.environ['CONFIG_FILE_NAME'] = configFilePath
    os.environ['RUN_FILE_NAME'] = runFilePath
    os.environ['MOOSE_OPT_PATH'] = os.path.join('~', 'projects', 'moose', 'moose_test-opt')
    didSucceed = template_parser.main()


def createConfigFile_scenario03():
    sys.argv = [os.path.join('adapter', 'template_parser.py')]
    os.environ['INPUT_FILE_NAME'] = os.getenv("INPUT_FILE_NAME")
    os.environ['CONFIG_FILE_NAME'] = os.getenv("CONFIG_FILE_NAME")
    os.environ['RUN_FILE_NAME'] = os.getenv("RUN_FILE_NAME")
    os.environ['OUTPUT_FILE_NAME'] = os.getenv("OUTPUT_FILE_NAME")
    os.environ['OUTPUT_FILE_WAIT_SECONDS'] = '2'
    os.environ['PYTHONPATH'] = moose_python
    os.environ['MOOSE_OPT_PATH'] = moose_executable
    os.environ['DEEP_LYNX_URL'] = 'http://127.0.0.1:8090'
    os.environ['CONTAINER_NAME'] = 'DIAMOND'
    os.environ['DATA_SOURCE_NAME'] = 'MOOSEAdapter'
    didSucceed = template_parser.main()


def test_createJSONData_exist():
    """Assert that a valid list of json objects was returned
        Test Case: Valid list of json objects that contain the correct information"""
    jsonData = moose_adapter.createJSONData()
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


def test_validateDataToChangeInInputFile_invalidNode():
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
    if os.path.isfile(os.getenv("OUTPUT_FILE_NAME")):
        os.remove(os.getenv("OUTPUT_FILE_NAME"))
    isOutputFile = moose_adapter.getOutputFile()
    assert isOutputFile == False
    deleteConfigFile()


def test_main_fail():
    """Assert that the MOOSE Adapter failed in running an input file in MOOSE
        Test Case: Failed MOOSE Adapter"""
    jsonData = [{"node": "/Mesh", "parameter": "nx", "value": 200}]
    createConfigFile_scenario03()
    ranMOOSE = moose_adapter.main(jsonData)
    assert ranMOOSE == False
