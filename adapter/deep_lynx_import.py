# Copyright 2021, Battelle Energy Alliance, LLC

import os
import json
import settings
import pandas as pd
import logging
import deep_lynx
import utils


def deep_lynx_import(dl_service: deep_lynx.DeepLynxService):
    """
    Imports data into Deep Lynx
    Args
        dl_service (DeepLynxService): deep lynx service object
    """
    # Location of file to read
    data_file = os.getenv("IMPORT_FILE_NAME")
    # Generate a dictionary of payloads to import
    payload = generate_payload(data_file)
    # Convert dictionary to list of payloads
    payload_list = list()
    for key in payload.keys():
        payload_list.extend(payload[key])
    # Manually import the data
    info = create_manual_import(dl_service, payload_list)
    if info and info['isError'] == False:
        logging.info("Successfully imported data to deep lynx")
        print("Successfully imported data to deep lynx")
    else:
        logging.error(info)
        print("Could not import data into Deep Lynx. Check log file for more information")


def create_manual_import(dl_service: deep_lynx.DeepLynxService = None, payload: list = None):
    """
    Creates a manual import of the payload to insert into Deep Lynx
    Args
        dl_service (DeepLynxService): deep lynx service object
        payload (list): a list of payloads to import into deep lynx
    """
    if dl_service and payload:
        return dl_service.create_manual_import(dl_service.container_id, dl_service.data_source_id, payload)


def upload_file(dl_service: deep_lynx.DeepLynxService, file_paths: list):
    """
    Uploads a file into Deep Lynx   
    Args
        file_paths (list): An array of strings with locations to each file
        to be uploaded.
    """
    return dl_service.upload_file(dl_service.container_id, dl_service.data_source_id, file_paths)


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
