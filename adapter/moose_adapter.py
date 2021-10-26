# Copyright 2021, Battelle Energy Alliance, LLC
import os
import logging
import json
import datetime
import time
import deep_lynx
import utils

import pyhit
import moosetree
import mooseutils


def createJSONData():
    """
    Creates dummy data from Deep Lynx
    """
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


def updateParameterValues(node: moosetree.Node, jsonObj: dict):
    """
    Updates the parameter value of a node and adds a comment documenting the change
    Args
        node (Node): a moosetree node
        jsonObj (dictionary): a json object from Deep Lynx
    """
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


def removeConfigComments(node: moosetree.Node):
    """
    Remove the "{{config}}" comments from the parameters of a node
    Args
        node (Node): a moosetree node
    """
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


def createInputFileToRun(jsonData: list):
    """
    Creates an input file that incorporates the modifications from Deep Lynx
    Args
        jsonData (list): an array of json objects from Deep Lynx
    """
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


def runInputFile():
    """
    Runs the input file in MOOSE
    """

    # Validate paths exist
    mooseOptPath = os.path.expanduser(os.getenv("MOOSE_OPT_PATH"))
    utils.validatePathsExist(mooseOptPath, os.getenv("RUN_FILE_NAME"))
    returnCode = mooseutils.run_executable(mooseOptPath, '-i', os.getenv("RUN_FILE_NAME"))
    if returnCode != 0:
        logging.error('Fail: Could not run MOOSE')
    else:
        logging.info('Success: The MOOSE Adapter used the MOOSE input file %s to generate the output file %s',
                     os.getenv('RUN_FILE_NAME'), os.getenv('OUTPUT_FILE_NAME'))
        return True
    return False


def main(jsonData=None, event=None, deepLynxService=None):
    """
    Main entry point for script
    """

    logging.info('MOOSE Adapter started. Using input file %s and configuration file %s', os.getenv('INPUT_FILE_NAME'),
                 os.getenv('CONFIG_FILE_NAME'))
    if jsonData is None:
        jsonData = createJSONData()
    isValidated = utils.validateChangesToInputFile(jsonData)
    if isValidated:
        createInputFileToRun(jsonData)
        # Run input file
        isRun = runInputFile()
    return False


if __name__ == '__main__':
    main()
