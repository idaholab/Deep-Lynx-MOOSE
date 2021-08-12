# Copyright 2021, Battelle Energy Alliance, LLC
import os
import logging
import json
import configparser
import datetime
import time
import deep_lynx

import pyhit
import moosetree
import mooseutils


def createJSONData():
    """Creates dummy data from Deep Lynx"""
    jsonData = [{
        "node": None,
        "parameter": "xmax",
        "value": 4
    }, {
        "node": "/Mesh/gen",
        "parameter": "nx",
        "value": 200
    }, {
        "node": "/BCs/left",
        "parameter": "value",
        "value": 200
    }]
    return jsonData


def validateDataToChangeInInputFile(jsonData):
    """Validate the json objects before changing the input file that will be run in MOOSE
            1. Return True: When all json objects are checked with a valid node, parameter, and datatype
            2. Return False: When a invalid node, parameter, or datatype was provided in a json object"""

    # Read the config file
    config = configparser.ConfigParser()
    read_files = config.read(os.getenv('CONFIG_FILE_NAME'))
    if os.getenv("CONFIG_FILE_NAME") in read_files:
        configNodes = config.sections()

        # Check each json object for a valid node, parameter, and datatype of value
        for jsonObj in jsonData:
            isNodeFound = False
            for configNode in configNodes:
                configParams = dict(config.items(configNode))
                # If a valid node: either subsection nodes or root node
                if jsonObj['node'] == configNode or (jsonObj['node'] == None and configNode == 'root'):
                    isNodeFound = True
                    isParameterFound = False
                    for configParam, configValue in configParams.items():
                        # If a valid parameter
                        if configParam == jsonObj['parameter']:
                            isParameterFound = True
                            # If a valid datatype
                            if type(jsonObj['value']).__name__ == configValue:
                                break
                            # Not a valid datatype
                            else:
                                logging.error(
                                    'Invalid parameter datatype from Deep Lynx: the object with the node(%s) and the parameter(%s) provided a value with an incorrect datatype(%s). The %s requires that %s be of datatype(%s)',
                                    configNode, configParam,
                                    type(jsonObj['value']).__name__, os.getenv('INPUT_FILE_NAME'), configParam,
                                    configValue)
                                return False
                    # Not a valid parameter
                    if not isParameterFound:
                        logging.error(
                            'Invalid Parameter from Deep Lynx: the object with the node(%s) and the parameter(%s) cannot be modified because the parameter is not specified in the configuration file. Modify %s or incoming data accordingly',
                            jsonObj['node'], jsonObj['parameter'], os.getenv('INPUT_FILE_NAME'))
                        return False
                    # Is a valid parameter, do not check other configNodes
                    else:
                        break
            # Not a valid node
            if not isNodeFound:
                logging.error(
                    'Invalid Node from Deep Lynx: the object with the node(%s) cannot be modified because the node is not specified in the configuration file. Modify %s or incoming data accordingly',
                    jsonObj['node'], os.getenv('INPUT_FILE_NAME'))
                return False
    else:
        logging.error("Failed to read configuration file %s", os.getenv("CONFIG_FILE_NAME"))
        return False
    # All json objects were validated
    return True


def updateParameterValues(node, jsonObj):
    """Updates the parameter value of a node and adds a comment documenting the change
        Inputs
            node: a moosetree node
            jsonObj: a json object from Deep Lynx"""
    parameters = dict(node.params())
    # Check if the json object is a subsection node or the root node
    if node.fullpath == jsonObj['node'] or (jsonObj['node'] == None and not node.fullpath):
        # Update the parameter value
        originalValue = node[jsonObj['parameter']]
        node[jsonObj['parameter']] = jsonObj['value']
        # Add a comment that details the changes made to the parameter
        # Note: Comment starts with the keyword "{{change}}" to distinguish between user comments
        for key, value in parameters.items():
            originalComment = node.comment(param=key)
            if originalComment is not None:
                if '{{config}}' in originalComment:
                    if key == jsonObj['parameter']:
                        newComment = originalComment + ' {{change}} Changed \'' + key + '\' from ' + str(
                            originalValue) + ' to ' + str(node[jsonObj['parameter']])
                        node.setComment(key, newComment)


def removeConfigComments(node):
    """Remove the "{{config}}" comments from the parameters of a node
        Inputs
            node: a moose tree node"""
    parameters = dict(node.params())
    for key, value in parameters.items():
        originalComment = node.comment(param=key)
        if originalComment is not None:
            # Remove entire comment
            if originalComment == '{{config}}':
                node.setComment(key, None)
            # Modify existing comment
            elif '{{config}}' in originalComment:
                modifiedComment = originalComment.replace('{{config}}', '').strip()
                node.setComment(key, modifiedComment)


def createInputFileToRun(jsonData):
    """Creates an input file that incorporates the modifications from Deep Lynx
        Inputs
            jsonData: an array of json objects from Deep Lynx"""
    # Read the file
    root = pyhit.load(os.getenv('INPUT_FILE_NAME'))
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))

    # Update parameter values for the new the input file and add a comment documenting the change
    for jsonObj in jsonData:
        # Update parameter values for the root node
        updateParameterValues(root, jsonObj)
        # Update parameter values for the subsection nodes
        for node in nodes:
            updateParameterValues(node, jsonObj)

    #  Remove the "{{config}}" comments from parameters in the root node
    removeConfigComments(root)
    # Remove the "{{config}}" comments for parameters in the subsection nodes
    for node in nodes:
        removeConfigComments(node)

    # Write the moosetree to a file
    pyhit.write(os.getenv('RUN_FILE_NAME'), root)


def validatePathsExist():
    """Fail safe check: validate whether the paths (MOOSE_OPT_PATH, RUN_FILE_NAME) exists before running MOOSE"""
    # Replaces an initial path component ~( tilde symbol) in the given path with the user’s home directory
    mooseOptPath = os.path.expanduser(os.getenv("MOOSE_OPT_PATH"))

    isValidMooseOptPath = False
    isValidRunFileName = False

    # Check whether the specified path exists for the MOOSE_OPT_PATH
    if os.path.exists(mooseOptPath):
        isValidMooseOptPath = True
    else:
        logging.error(
            'Invalid path: the specified path(%s) of the "MOOSE_OPT_PATH" environment variable in .env file does not exist',
            os.getenv("MOOSE_OPT_PATH"))

    # Check whether the specified path exists for the RUN_FILE_NAME
    if os.path.exists(os.getenv("RUN_FILE_NAME")):
        isValidRunFileName = True
    else:
        logging.error(
            'Invalid path: the specified path(%s) of the "RUN_FILE_NAME" environment variable in .env file does not exist',
            os.getenv("RUN_FILE_NAME"))

    if isValidMooseOptPath and isValidRunFileName:
        return True
    else:
        return False


def runInputFile():
    """Runs the input file in MOOSE"""

    mooseOptPath = os.path.expanduser(os.getenv("MOOSE_OPT_PATH"))
    isValidated = validatePathsExist()
    if isValidated:
        returnCode = mooseutils.run_executable(mooseOptPath, '-i', os.getenv("RUN_FILE_NAME"))
        if returnCode != 0:
            logging.error('Fail: Could not run MOOSE')
        else:
            logging.info('Success: The MOOSE Adapter used the MOOSE input file %s to generate the output file %s',
                         os.getenv('RUN_FILE_NAME'), os.getenv('OUTPUT_FILE_NAME'))
            return True
    else:
        logging.error('Fail safe: Failed to validate paths. The input file was not run in MOOSE.')
    return False


def getOutputFile(event=None):
    """Checks for the json output file generated by MOOSE"""
    done = False
    didSucceed = False
    wait = 5
    start = time.time()
    while not done:
        if os.path.exists(os.path.join(os.getcwd() + '/' + os.getenv('OUTPUT_FILE_NAME'))):

            with open(os.getenv('OUTPUT_FILE_NAME')) as json_file:
                moose_output = json.load(json_file)

                logging.info(f'Found {os.getenv("OUTPUT_FILE_NAME")}. Updating event and sending both to Deep Lynx.')
                dlService = deep_lynx.DeepLynxService(os.getenv('DEEP_LYNX_URL'), os.getenv('CONTAINER_NAME'),
                                                      os.getenv('DATA_SOURCE_NAME'))
                if event is not None:
                    # send event signaling MOOSE is done
                    event['status'] = 'complete'
                    event['modifiedDate'] = datetime.datetime.now().isoformat()
                    dlService.create_manual_import(dlService.container_id, dlService.data_source_id, event)
                    logging.info('Event sent.')

                # send data to Deep Lynx
                dlService.create_manual_import(dlService.container_id, dlService.data_source_id, moose_output)
                logging.info('Success: Run complete. Output data sent.')

                done = True
                didSucceed = True
                break
        else:
            logging.info(f'Fail: {os.getenv("OUTPUT_FILE_NAME")} not found. Trying again in {wait} seconds')
            end = time.time()
            if end - start > float(os.getenv('OUTPUT_FILE_WAIT_SECONDS')):
                done = True
                break
            else:
                time.sleep(wait)
    if didSucceed:
        return True
    return False


def main(jsonData=None, event=None, deepLynxService=None):
    """ Main entry point for script. """

    logging.info('MOOSE Adapter started. Using input file %s and configuration file %s', os.getenv('INPUT_FILE_NAME'),
                 os.getenv('CONFIG_FILE_NAME'))
    if jsonData is None:
        jsonData = createJSONData()
    isValidated = validateDataToChangeInInputFile(jsonData)
    if isValidated:
        createInputFileToRun(jsonData)
        isRun = runInputFile()
        if isRun:
            isOutputFile = getOutputFile(event)
            if isOutputFile:
                return True
    return False


if __name__ == '__main__':
    main()
