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
from adapter.deep_lynx_query import deep_lynx_init

import mooseutils


def queryDeepLynx(api_client: deep_lynx.ApiClient = None, dl_events: list = None):
    """
    Query Deep Lynx for data
    Args
        api_client (ApiClient): deep lynx api client
        dl_event (list): a list of json objects from a deep lynx event
    Return
        True: if query file is found
        False: query file is not found
    """
    done = False
    didSucceed = False
    start = time.time()

    data_query_api = None
    if api_client is not None:
        data_query_api = deep_lynx.DataQueryApi(api_client)

    deep_lynx_query(data_query_api, dl_events)
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


def importToDeepLynx(api_client: deep_lynx.ApiClient = None,
                     container_id: str = '',
                     data_source_id: str = '',
                     event: dict = None):
    """
    Imports the results into Deep Lynx
    Args
        api_client (ApiClient): deep lynx api client
        container_id (str): deep lynx container id
        data_source_id (str): deep lynx data source id
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
            data_sources_api = deep_lynx.DataSourcesApi(api_client)
            deep_lynx_import(data_sources_api, container_id, data_source_id)
            logging.info('Success: Run complete. Output data sent.')

            if event:
                # Send event signaling MOOSE is done
                event['status'] = 'complete'
                event['modifiedDate'] = datetime.datetime.now().isoformat()
                data_sources_api.create_manual_import(event, container_id, data_source_id)
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


def main(dl_event=None, api_client: deep_lynx.ApiClient = None, container_id: str = '', data_source_id: str = ''):
    """
    Main entry point for script
    Args
        api_client (ApiClient): deep lynx api client
        container_id (str): deep lynx container id
        data_source_id (str): deep lynx data source id
    """

    logging.info('MOOSE Adapter started. Using input file %s and configuration file %s',
                 os.getenv('CONFIG_INPUT_FILE_NAME'), os.getenv('CONFIG_FILE_NAME'))

    # instantiate deep_lynx client if necessary
    if api_client is None:
        container_id, data_source_id, api_client = deep_lynx_init()

    doesQueryFileExist = queryDeepLynx(api_client, container_id, data_source_id, dl_event)
    if doesQueryFileExist:
        isRun = runInputFile()
    if isRun:
        createOutputFile()
        isImported = importToDeepLynx(api_client, container_id, data_source_id)
        return isImported
    return False


if __name__ == '__main__':
    main()
