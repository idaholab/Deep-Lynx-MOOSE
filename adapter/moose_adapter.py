# Copyright 2021, Battelle Energy Alliance, LLC

import os
import logging
import datetime
import time
import pandas as pd
import deep_lynx

import utils
from adapter.deep_lynx_query import deep_lynx_query
from adapter.deep_lynx_import import deep_lynx_import
import settings

import pyhit
import moosetree
import mooseutils


def queryDeepLynx(dlService: deep_lynx.DeepLynxService = None):
    """
    Query Deep Lynx for data
    Args
        dl_service (DeepLynxService): deep lynx service object
    Return
        True: if query file is found
        False: query file is not found
    """
    done = False
    didSucceed = False
    start = time.time()
    deep_lynx_query(dlService)
    path = os.path.join(os.getcwd() + '/' + os.getenv('QUERY_FILE_NAME'))
    while not done:
        # Check if query file exists
        if os.path.exists(path):
            logging.info(f'Found {os.getenv("QUERY_FILE_NAME")}.')
            done = True
            didSucceed = True
            break
        else:
            logging.info(
                f'Fail: {os.getenv("QUERY_FILE_NAME")} not found. Trying again in {os.getenv("QUERY_FILE_WAIT_SECONDS")} seconds'
            )
            end = time.time()
            # Break out of infinite loop
            if end - start > float(os.getenv("QUERY_FILE_WAIT_SECONDS")) * 20:
                logging.info(f'Fail: In the final attempt, {os.getenv("QUERY_FILE_NAME")} was not found.')
                done = True
                break
            # Sleep for wait seconds
            else:
                logging.info(
                    f'Fail: {os.getenv("QUERY_FILE_NAME")} was not found. Trying again in {os.getenv("QUERY_FILE_WAIT_SECONDS")} seconds'
                )
                time.sleep(int(os.getenv("QUERY_FILE_WAIT_SECONDS")))
    if didSucceed:
        return True
    return False


def runInputFile():
    """
    Runs the input file in MOOSE
    """
    # Validate paths exist
    mooseOptPath = os.path.expanduser(os.getenv("MOOSE_OPT_PATH"))
    utils.validatePathsExist(mooseOptPath, os.getenv("RUN_FILE_NAME"))
    # Run input file in MOOSE
    returnCode = mooseutils.run_executable(mooseOptPath, '-i', os.getenv("RUN_FILE_NAME"))
    if returnCode != 0:
        logging.error('Fail: Could not run MOOSE')
    else:
        logging.info('Success: The MOOSE Adapter used the MOOSE input file %s to generate the output file %s',
                     os.getenv('RUN_FILE_NAME'), os.getenv('IMPORT_FILE_NAME'))
        return True
    return False


def createOutputFile():
    """
    Parses the file(s) produced by the MOOSE executable into an output file to send back to Deep Lynx
    """
    results = pd.DataFrame()
    # Write the MOOSE results to csv file
    results.to_csv(os.getenv("IMPORT_FILE_NAME"), index=False)


def importToDeepLynx(dlService: deep_lynx.DeepLynxService = None, event: dict = None):
    """
    Imports the results into Deep Lynx
    Args
        dl_service (DeepLynxService): deep lynx service object
        event (dictionary): a dictionary of the event information
    """
    done = False
    didSucceed = False
    start = time.time()
    path = os.path.join(os.getcwd() + '/' + os.getenv('IMPORT_FILE_NAME'))
    while not done:
        # Check if query file exists
        if os.path.exists(path):
            logging.info(f'Found {os.getenv("IMPORT_FILE_NAME")}.')
            # Import data into Deep Lynx
            deep_lynx_import(dlService)
            logging.info('Success: Run complete. Output data sent.')

            if event:
                # Send event signaling MOOSE is done
                event['status'] = 'complete'
                event['modifiedDate'] = datetime.datetime.now().isoformat()
                dlService.create_manual_import(dlService.container_id, dlService.data_source_id, event)
                logging.info('Event sent.')
            done = True
            didSucceed = True
            break
        else:
            logging.info(
                f'Fail: {os.getenv("IMPORT_FILE_NAME")} not found. Trying again in {os.getenv("IMPORT_FILE_WAIT_SECONDS")} seconds'
            )
            end = time.time()
            # Break out of infinite loop
            if end - start > float(os.getenv("IMPORT_FILE_WAIT_SECONDS")) * 20:
                logging.info(f'Fail: In the final attempt, {os.getenv("IMPORT_FILE_NAME")} was not found.')
                done = True
                break
            # Sleep for wait seconds
            else:
                logging.info(
                    f'Fail: {os.getenv("IMPORT_FILE_NAME")} was not found. Trying again in {os.getenv("IMPORT_FILE_WAIT_SECONDS")} seconds'
                )
                time.sleep(int(os.getenv("IMPORT_FILE_WAIT_SECONDS")))
    if didSucceed:
        return True
    return False


def main(event=None, dlService=None):
    """
    Main entry point for script
    """

    logging.info('MOOSE Adapter started. Using input file %s and configuration file %s',
                 os.getenv('CONFIG_INPUT_FILE_NAME'), os.getenv('CONFIG_FILE_NAME'))
    doesQueryFileExist = queryDeepLynx(dlService)
    if doesQueryFileExist:
        isRun = runInputFile()
    if isRun:
        createOutputFile()
        isImported = importToDeepLynx(dlService)
        return isImported
    return False


if __name__ == '__main__':
    main()
