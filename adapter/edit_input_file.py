# Copyright 2021, Battelle Energy Alliance, LLC

import os
import logging
import configparser
import settings

from adapter import template_parser

import pyhit
import moosetree
import mooseutils


def createJSONData():
    """
    Creates dummy data from Deep Lynx
    Args
        jsonData (dictionary): a dictionary of dummy data
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


def validateChangesToInputFile(jsonData: list):
    """
    Validate the json objects before changing the input file that will be run in MOOSE
    Args
        jsonData (list): an array of json objects from Deep Lynx
    Return
        True: When all json objects are checked with a valid node, parameter, and datatype
        False: When a invalid node, parameter, or datatype was provided in a json object
    """

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
                                    type(jsonObj['value']).__name__, os.getenv('CONFIG_INPUT_FILE_NAME'), configParam,
                                    configValue)
                                return False
                    # Not a valid parameter
                    if not isParameterFound:
                        logging.error(
                            'Invalid Parameter from Deep Lynx: the object with the node(%s) and the parameter(%s) cannot be modified because the parameter is not specified in the configuration file. Modify %s or incoming data accordingly',
                            jsonObj['node'], jsonObj['parameter'], os.getenv('CONFIG_INPUT_FILE_NAME'))
                        return False
                    # Is a valid parameter, do not check other configNodes
                    else:
                        break
            # Not a valid node
            if not isNodeFound:
                logging.error(
                    'Invalid Node from Deep Lynx: the object with the node(%s) cannot be modified because the node is not specified in the configuration file. Modify %s or incoming data accordingly',
                    jsonObj['node'], os.getenv('CONFIG_INPUT_FILE_NAME'))
                return False
    else:
        logging.error("Failed to read configuration file %s", os.getenv("CONFIG_FILE_NAME"))
        return False
    # All json objects were validated
    return True


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


def modifyInputFile(jsonData: list):
    """
    Creates an input file that incorporates the modifications from Deep Lynx
    Args
        jsonData (list): an array of json objects from Deep Lynx
    """
    # Read the file
    root = pyhit.load(os.getenv('CONFIG_INPUT_FILE_NAME'))
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


def main(jsonData=None, event=None, dlService=None):
    """
    Main entry point for script
    """

    if jsonData is None:
        #jsonData = createJSONData()
        jsonData = [{"node": "/A", "parameter": "year", "value": 2000}]
    if not os.path.exists(os.getenv("CONFIG_FILE_NAME")):
        template_parser.main()
    isValidated = validateChangesToInputFile(jsonData)
    #if isValidated:
    #modifyInputFile(jsonData)


if __name__ == '__main__':
    main()
