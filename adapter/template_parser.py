# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import os
import logging
import argparse
import configparser

# Repository Modules
import utils
import settings

# MOOSE Modules
import pyhit
import moosetree


def get_parser_arguments():
    """
    Gets the arguments provided by the user via the command-line
    Return 
        args: the arguments provided by the user and parsed by the Argument Parser
    """
    # Create command-line interface
    parser = argparse.ArgumentParser(prefix_chars='-',
                                     description='Provide a MOOSE input file (.i) to generate a configuration file',
                                     add_help=False)
    options = parser.add_argument_group(title='Options')
    options.add_argument('-i', metavar='<input_file>', dest='input_file', help='Specify a MOOSE input file', nargs=1)
    options.add_argument('-h', '--help', action='help', help='Displays CLI usage statement')
    args, unknown = parser.parse_known_args()
    # Validate the input file has ".i" extension
    if args.input_file:
        utils.validate_extension(".i", args.input_file[0])
    return args


def get_input_file_path(args):
    """
    Gets the path to the input file
    Return
        input_file (string): the file path to the input file 
        is_env_variable (bool): whether using the .env file or not (command-line)  
    """
    is_env_variable = False
    # Determine the input file depending on the use of the command-line interface
    if args.input_file is not None:
        input_file = args.input_file[0]
    else:
        input_file = os.getenv("TEMPLATE_INPUT_FILE_NAME")
        is_env_variable = True
    return input_file, is_env_variable


def get_config_file_name(input_file: str = None):
    """
    Returns the name of the config file
    Args
        input_file (string): the path to use for the config filename (command-line only)
    Return
        config_file (string): the file path to the config file    
    """
    if input_file:
        base, extension = os.path.splitext(input_file)
        config_file = '.'.join([base, 'cfg'])
    else:
        config_file = os.getenv("CONFIG_FILE_NAME")
    return config_file


def get_params_of_node(node: moosetree.Node, root: moosetree.Node):
    """
    Determine the parameters that can be modified which have a comment with '{{config}})'
    Args
        node (Node): a moosetree node
        root (Node): the root moosetree node
    Return
        section (string): the full path of the node
        paramDict (dictionary): dictionary of key, value pairs of the parameter name and the datatype
    """

    # Get the key, value for the parameters of this node
    node_parameters = dict(node.params())
    if root:
        root_parameters = dict(root.params())
    params_dict = dict()
    # Determine parameters with the comment {{config}} to add to the config file
    for node_key, node_value in node_parameters.items():
        comment = node.comment(param=node_key)
        if comment is not None:
            if '{{config}}' in comment:
                if isinstance(node_value, str):
                    # If value is a global variable at top of input file, use the datatype of the parameter from configDict
                    # Purpose: type('${xmax}') = str but should be int
                    if '${' in node_value:
                        modified_value = node_value.replace('${', '')
                        modified_value = modified_value.replace('}', '')
                        for root_key, root_value in root_parameters.items():
                            if root_key == modified_value:
                                params_dict[node_key] = type(root_value).__name__
                    else:
                        params_dict[node_key] = type(node_value).__name__
                else:
                    params_dict[node_key] = type(node_value).__name__

    # Return sections and a dictionary of parameters
    if len(params_dict) != 0:
        if node.fullpath:
            section = node.fullpath
        else:
            section = 'root'
        return section, params_dict


def get_config_parameters(input_file: str):
    """
    Determine the section and parameters for the configuration file
    Args
        input_file (string): the input file for pyhit to read
    Return
        config_params (dictionary): a dictionary of configuration parameters {section: dict(parameter name: datatype of value)}
    """

    config_params = dict()
    # Read the file
    root = pyhit.load(input_file)
    # Get nodes
    nodes = list(moosetree.iterate(root, method=moosetree.IterMethod.PRE_ORDER))

    # For root node: Determine global variables with the comment {{config}} to add to the config file
    section, params_dict = get_params_of_node(root, None) or (None, None)
    if section and params_dict:
        config_params[section] = params_dict

    # For subsection nodes: Determine parameters with the comment {{config}} to add to the config file
    for node in nodes:
        section, params_dict = get_params_of_node(node, root) or (None, None)
        if section and params_dict:
            config_params[section] = params_dict
    return config_params


def write_config_file(config_params: dict, config_file: str):
    """
    Write the config parameters to a configuration file
    Args
        config_params (dictionary): a dictionary of configuration parameters {section: dict(parameter name: datatype of value)}
        config_file (string): name of the configuration file to write
    Return
        True: if config file path exists
        False: if config file path does not exist
    """

    config = configparser.ConfigParser()
    config.optionxform = str
    for key, value in config_params.items():
        config[key] = value
    # Write config to file
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        if os.path.exists(config_file):
            return True
    return False


def main():
    """ Main entry point for script 
    Return
        True: if successfully generated a configuration file
        False: if invalid input file
    """
    args = get_parser_arguments()
    input_file, is_env_variable = get_input_file_path(args)
    utils.validate_paths_exist(input_file)
    if is_env_variable:
        logging.info('Template Parser started. Using input file %s', os.getenv('CONFIG_FILE_NAME'))
        config_file = get_config_file_name()
    else:
        config_file = get_config_file_name(input_file)
    config_params = get_config_parameters(input_file)
    is_config_file_created = write_config_file(config_params, config_file)
    if is_config_file_created:
        if is_env_variable:
            logging.info(
                'Success: The Template Parser used the MOOSE input file %s to generate a configuration file %s',
                os.getenv('CONFIG_FILE_NAME'), os.getenv('CONFIG_FILE_NAME'))
        else:
            print('Success: The provided MOOSE input file %s generated a configuration file %s' %
                  (input_file, config_file))
        return True
    else:
        if is_env_variable:
            logging.error('Fail: Provide a valid path to a MOOSE input file (.i) to generate a configuration file')
        else:
            print('Fail: Provide a valid path to a MOOSE input file (.i) to generate a configuration file')
        return False


if __name__ == '__main__':
    main()
