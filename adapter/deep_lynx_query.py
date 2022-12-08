# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import os
import pandas as pd
import deep_lynx

# Repository Modules
import settings
import adapter


def query_deep_lynx(file_id: str):
    """
    Retrieve data from Deep Lynx
    Args
        file_id (string): the id of a file stored in Deep Lynx
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    # Retrieve file from Deep Lynx
    data_sources_api = deep_lynx.DataSourcesApi(api_client)
    dl_file_path = retrieve_file(data_sources_api, file_id)

    # Write csv to local repository
    query_df = pd.read_csv(dl_file_path)
    queue(query_df)


def download_file(dl_service: deep_lynx.DataSourcesApi, file_id: str):
    """
    Downloads a file from Deep Lynx
    Args
        dl_service (deep_lynx.DataSourcesApi): deep lynx data source api
        file_id (string): the id of a file
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    download_file = dl_service.download_file(container_id, file_id)

    if not download_file.is_error:
        return download_file


def retrieve_file(data_sources_api: deep_lynx.DataSourcesApi, file_id: str):
    """
    Retrieve a file from Deep Lynx
    Args
        data_sources_api (deep_lynx.DataSourcesApi): deep lynx data source api
        file_id (string): the id of a file
        container_id (str): deep lynx container id
    """
    # Get deep lynx environment variables
    api_client = adapter.api_client
    container_id = os.environ["CONTAINER_ID"]
    data_source_id = os.environ["DATA_SOURCE_ID"]

    retrieve_file = data_sources_api.retrieve_file(container_id, file_id)

    if not retrieve_file.is_error:
        retrieve_file = retrieve_file.to_dict()["value"]
        path = retrieve_file["adapter_file_path"] + retrieve_file["file_name"]
        return path


def queue(query_df: pd.DataFrame or pd.Series):
    """
    Maintains a queue file of a given length via the First In First Out (FIFO) data structure
    Args
        query_df (DataFrame or Series): data to add to the queue
    """
    # Applies a lock for threading
    with adapter.lock_:
        if os.path.exists(os.getenv("QUEUE_FILE_NAME")):
            # Read master queue file
            queue_df = pd.read_csv(os.getenv("QUEUE_FILE_NAME"))
            # Append query file to queue
            queue_df = queue_df.append(query_df, ignore_index=True)
        else:
            # If queue file does not exist
            queue_df = query_df
        new_queue_length = queue_df.shape[0]
        # Keep queue at given length
        if new_queue_length > int(os.getenv("QUEUE_LENGTH")):
            subtract_length = new_queue_length - int(os.getenv("QUEUE_LENGTH"))
            queue_df.drop([i for i in range(subtract_length)], axis=0, inplace=True)
        # Write queue to csv
        queue_df.to_csv(os.getenv("QUEUE_FILE_NAME"), index=False)
