# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import os
import logging
import datetime
import time
import pandas as pd
import deep_lynx

# Repository Modules
import settings
import utils
import adapter
from .deep_lynx_import import import_to_deep_lynx

# MOOSE Modules
import mooseutils


def run_input_file():
    """
    Runs the input file in MOOSE
    """
    # Validate paths exist
    moose_opt_path = os.path.expanduser(os.getenv("MOOSE_OPT_PATH"))
    utils.validate_paths_exist(moose_opt_path, os.getenv("RUN_FILE_NAME"))
    # Run input file in MOOSE
    return_code = mooseutils.run_executable(moose_opt_path, '-i', os.getenv("RUN_FILE_NAME"))
    if return_code != 0:
        logging.error('Fail: Could not run MOOSE')
    else:
        logging.info('Success: The MOOSE Adapter used the MOOSE input file %s to generate the output file %s',
                     os.getenv('RUN_FILE_NAME'), os.getenv('IMPORT_FILE_NAME'))
        return True
    return False


def create_output_file():
    """
    Parses the file(s) produced by the MOOSE executable into an output file to send back to Deep Lynx
    """
    results = pd.DataFrame()
    # Write the MOOSE results to csv file
    results.to_csv(os.getenv("IMPORT_FILE_NAME"), index=False)


def main():
    """
    Main entry point for script
    Args
        None
    """

    logging.info('MOOSE Adapter started. Using input file %s and configuration file %s',
                 os.getenv('TEMPLATE_INPUT_FILE_NAME'), os.getenv('CONFIG_FILE_NAME'))
    done = False
    while not done:
        if os.path.exists(os.getenv("QUEUE_FILE_NAME")) and adapter.new_data:
            # Apply a lock
            with adapter.lock_:
                adapter.new_data = False
                # Read master queue file
                queue_df = pd.read_csv(os.getenv("QUEUE_FILE_NAME"))
            # Only execute if queue reaches optimal length
            if queue_df.shape[0] == int(os.getenv("QUEUE_LENGTH")):

                # TODO: Change to customized name
                query_file_name = None
                import_file_name = None

                #Set environment variables
                os.environ["QUERY_FILE_NAME"] = query_file_name
                os.environ["IMPORT_FILE_NAME"] = import_file_name

                # Write csv
                queue_df.to_csv(query_file_name, index=False)

                # TODO: Update input file by calling edit_input_file.py

                # Run MOOSE
                start = time.time()
                is_run = run_input_file()
                end = time.time()
                print(end - start)

                if is_run:
                    create_output_file()
                    # Import the results to deep lynx
                    print("Begin import to deep lynx")
                    is_imported = import_to_deep_lynx(os.getenv("IMPORT_FILE_NAME"))
                    print("Deep Lynx Import", is_imported)

                # File cleanup
                if is_run and is_imported:
                    if os.path.exists(os.getenv("QUERY_FILE_NAME")):
                        os.remove(os.getenv("QUERY_FILE_NAME"))
                    if os.path.exists(os.getenv("IMPORT_FILE_NAME")):
                        os.remove(os.getenv("IMPORT_FILE_NAME"))
                    if os.path.exists("data/sphere_csv.csv"):
                        os.remove("data/sphere_csv.csv")
                    if os.path.exists("data/sphere_out.e"):
                        os.remove("data/sphere_out.e")


if __name__ == '__main__':
    main()
