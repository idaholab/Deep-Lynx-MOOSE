# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import os
import logging
import deep_lynx
import json
import time

# Repository Modules
import adapter


def import_to_deep_lynx(import_file: str):
    """
    Import data into Deep Lynx
    Args
        import_file (string): the file path to import into Deep Lynx
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    done = False
    did_succeed = False
    start = time.time()
    path = os.path.join(os.getcwd() + '/' + import_file)
    while not done:
        # Check if import file exists
        if os.path.exists(path):
            logging.info(f'Found {import_file}.')
            # Import data into Deep Lynx
            data_sources_api = deep_lynx.DataSourcesApi(api_client)
            info = upload_file(data_sources_api, import_file)
            logging.info('Success: Run complete. Output data sent.')
            done = True
            did_succeed = True
            break
        else:
            logging.info(
                f'Fail: {import_file} not found. Trying again in {os.getenv("IMPORT_FILE_WAIT_SECONDS")} seconds')
            end = time.time()
            # Break out of infinite loop
            if end - start > float(os.getenv("IMPORT_FILE_WAIT_SECONDS")) * 20:
                logging.info(f'Fail: In the final attempt, {import_file} was not found.')
                done = True
                break
            # Sleep for wait seconds
            else:
                logging.info(
                    f'Fail: {import_file} was not found. Trying again in {os.getenv("IMPORT_FILE_WAIT_SECONDS")} seconds'
                )
                time.sleep(int(os.getenv("IMPORT_FILE_WAIT_SECONDS")))
    if did_succeed:
        return True
    return False


def upload_file(data_sources_api: deep_lynx.DataSourcesApi, file_path: str):
    """
    Uploads a file into Deep Lynx   
    Args
        data_sources_api (deep_lynx.DataSourcesApi): deep lynx data source api
        file_path (string): the file path to import into Deep Lynx
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    file_return = data_sources_api.upload_file(container_id,
                                               data_source_id,
                                               file=file_path,
                                               metadata=os.getenv("METADATA_FILE_NAME"),
                                               async_req=False)
    if len(file_return["value"]) > 0:
        logging.info("Successfully imported data to deep lynx")
        print("Successfully imported data to deep lynx")
    else:
        logging.error("Could not import data into Deep Lynx. Check log file for more information")
        print("Could not import data into Deep Lynx. Check log file for more information")
    return file_return


def create_manual_import(data_sources_api: deep_lynx.DataSourcesApi = None, payload: list = None):
    """
    Creates a manual import of the payload to insert into Deep Lynx
    Args
        data_sources_api (deep_lynx.DataSourcesApi): deep lynx data source api
        payload (list): a list of payloads to import into deep lynx
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    if data_sources_api and payload:
        return data_sources_api.create_manual_import(body=payload,
                                                     container_id=container_id,
                                                     data_source_id=data_source_id)


def generate_payload(data_file: str):
    """
    Generate a list of payloads to import into deep lynx
    
    Args
        data_file (string): location of file to read
    Return
        payload (dictionary): a dictionary of payloads to import into deep lynx e.g. {metatype: list(payload)}
    """
    payload = dict()
    return payload


def validate_payload(payload: dict):
    """
    Validates the payload before inserting into deep lynx
    
    Args
        payload (dictionary): a dictionary of payloads to import into deep lynx e.g. {metatype: list(payload)}

    Return
        is_valid (boolean): whether the payload is valid or not
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    # Create deep lynx validator object
    metatypes_api = deep_lynx.MetatypesApi(api_client)
    is_valid = True
    for metatype, nodes in payload.items():
        for node in nodes:
            # For each node, validate the its properies
            # assumes the first return is the desired metatype
            metatype_id = metatypes_api.list_metatypes(container_id, name=metatype)[0].id
            json_error = metatypes_api.validate_metatype_properties(container_id, metatype_id, node)
            json_error = json.loads(json_error)
            if json_error["isError"]:
                for error in json_error["error"]:
                    logging.error(error)
                    is_valid = False
    return is_valid
