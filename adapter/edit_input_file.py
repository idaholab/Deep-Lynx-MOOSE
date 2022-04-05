# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import os
import logging
import configparser

# Repository Modules
from adapter import template_parser
import settings

# MOOSE Modules
import pyhit
import moosetree
import mooseutils


def create_json_data():
    """
    Creates dummy data from Deep Lynx
    Args
        None
    """
    json_data = [{
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
    return json_data


def validate_changes_to_input_file(json_data: list):
    """
    Validate the json objects before changing the input file that will be run in MOOSE
    Args
        json_data (list): an array of json objects from Deep Lynx
    Return
        True: When all json objects are checked with a valid node, parameter, and datatype
        False: When a invalid node, parameter, or datatype was provided in a json object
    """

    # Read the config file
    config = configparser.ConfigParser()
    config.optionxform = str
    read_files = config.read(os.getenv('CONFIG_FILE_NAME'))
    if os.getenv("CONFIG_FILE_NAME") in read_files:
        config_nodes = config.sections()
        # Check each json object for a valid node, parameter, and datatype of value
        for json_object in json_data:
            is_node_found = False
            for config_node in config_nodes:
                config_params = dict(config.items(config_node))
                # If a valid node: either subsection nodes or root node
                if json_object['node'] == config_node or (json_object['node'] == None and config_node == 'root'):
                    is_node_found = True
                    is_parameter_found = False
                    for config_param, config_value in config_params.items():
                        # If a valid parameter
                        if config_param == json_object['parameter']:
                            is_parameter_found = True
                            # If a valid datatype
                            if config_value in type(json_object['value']).__name__:
                                break
                            # Not a valid datatype
                            else:
                                logging.error(
                                    'Invalid parameter datatype from Deep Lynx: the object with the node(%s) and the parameter(%s) provided a value with an incorrect datatype(%s). The %s requires that %s be of datatype(%s)',
                                    config_node, config_param,
                                    type(json_object['value']).__name__, os.getenv('CONFIG_FILE_NAME'), config_param,
                                    config_value)
                                return False
                    # Not a valid parameter
                    if not is_parameter_found:
                        logging.error(
                            'Invalid Parameter from Deep Lynx: the object with the node(%s) and the parameter(%s) cannot be modified because the parameter is not specified in the configuration file. Modify %s or incoming data accordingly',
                            json_object['node'], json_object['parameter'], os.getenv('CONFIG_FILE_NAME'))
                        return False
                    # Is a valid parameter, do not check other config_nodes
                    else:
                        break
            # Not a valid node
            if not is_node_found:
                logging.error(
                    'Invalid Node from Deep Lynx: the object with the node(%s) cannot be modified because the node is not specified in the configuration file. Modify %s or incoming data accordingly',
                    json_object['node'], os.getenv('CONFIG_FILE_NAME'))
                return False
    else:
        logging.error("Failed to read configuration file %s", os.getenv("CONFIG_FILE_NAME"))
        return False
    # All json objects were validated
    return True


def update_parameter_values(node: moosetree.Node, json_object: dict):
    """
    Updates the parameter value of a node and adds a comment documenting the change
    Args
        node (Node): a moosetree node
        json_object (dictionary): a json object from Deep Lynx
    """
    parameters = dict(node.params())
    # Check if the json object is a subsection node or the root node
    if node.fullpath == json_object['node'] or (json_object['node'] == None and not node.fullpath):
        # Update the parameter value
        original_value = node[json_object['parameter']]
        node[json_object['parameter']] = json_object['value']
        # Add a comment that details the changes made to the parameter
        # Note: Comment starts with the keyword "{{change}}" to distinguish between user comments
        for key, value in parameters.items():
            original_comment = node.comment(param=key)
            if original_comment is not None:
                if '{{config}}' in original_comment:
                    if key == json_object['parameter']:
                        newComment = original_comment + ' {{change}} Changed \'' + key + '\' from ' + str(
                            original_value) + ' to ' + str(node[json_object['parameter']])
                        node.setComment(key, newComment)


def remove_config_comments(node: moosetree.Node):
    """
    Remove the "{{config}}" comments from the parameters of a node
    Args
        node (Node): a moosetree node
    """
    parameters = dict(node.params())
    for key, value in parameters.items():
        original_comment = node.comment(param=key)
        if original_comment is not None:
            # Remove entire comment
            if original_comment == '{{config}}':
                node.setComment(key, None)
            # Modify existing comment
            elif '{{config}}' in original_comment:
                modified_comment = original_comment.replace('{{config}}', '').strip()
                node.setComment(key, modified_comment)


def modify_input_file(json_data: list):
    """
    Creates an input file that incorporates the modifications from Deep Lynx
    Args
        json_data (list): an array of json objects from Deep Lynx
    """
    # Read the file
    root = pyhit.load(os.getenv('TEMPLATE_INPUT_FILE_NAME'))
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))

    # Update parameter values for the new the input file and add a comment documenting the change
    for json_object in json_data:
        # Update parameter values for the root node
        update_parameter_values(root, json_object)
        # Update parameter values for the subsection nodes
        for node in nodes:
            update_parameter_values(node, json_object)

    #  Remove the "{{config}}" comments from parameters in the root node
    remove_config_comments(root)
    # Remove the "{{config}}" comments for parameters in the subsection nodes
    for node in nodes:
        remove_config_comments(node)

    # Write the moosetree to a file
    pyhit.write(os.getenv('RUN_FILE_NAME'), root)


def main(json_data=None, event=None, dlService=None):
    """
    Main entry point for script
    """

    if json_data is None:
        #json_data = create_json_data()
        json_data = [{"node": "/A", "parameter": "year", "value": 2000}]

    template_parser.main()
    is_validated = validate_changes_to_input_file(json_data)
    if is_validated:
        modify_input_file(json_data)


if __name__ == '__main__':
    main()
