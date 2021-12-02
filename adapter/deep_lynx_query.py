# Copyright 2021, Battelle Energy Alliance, LLC

import os
import json
import settings
import pandas as pd
import deep_lynx


def deep_lynx_query(dl_service: deep_lynx.DataQueryApi = None, dl_events: list = None):
    """
    Queries deep lynx for data and writes the dataset to .csv file
    Args
        dl_service (deep_lynx.DataQueryApi): deep lynx query api
        dl_events (list): a list of json objects from a deep lynx event
    """
    if dl_service:
        # Location of the file to write
        data_file = os.getenv("QUERY_FILE_NAME")
        # Compile data by querying Deep Lynx
        dataset = compile_data(dl_service)
        # Write dataset to csv file
        write_csv(dataset, data_file)


def query(dl_service: deep_lynx.DataQueryApi, payload: str, container_id: str):
    """
    Queries Deep Lynx for nodes or edges
    Args
        dl_service (deep_lynx.DataQueryApi): deep lynx query api
        payload (string): the graphQL query
        container_id (str): deep lynx container id
    Return 
        data (dictionary): a dictionary of nodes or edges
        
    """
    data = dl_service.query_graph(body=payload, container_id=container_id)
    return data


def download_file(dl_service: deep_lynx.DataSourcesApi, file_id: str, container_id: str):
    """
    Downloads a file from Deep Lynx
    Args
        dl_service (deep_lynx.DataSourcesApi): deep lynx data source api
        file_id (string): the id of a file
        container_id (str): deep lynx container id
    """
    return dl_service.download_file(container_id=container_id, file_id=file_id)


def retrieve_file(dl_service: deep_lynx.DataSourcesApi, file_id: str, container_id: str):
    """
    Retrieves a file from Deep Lynx
    Args
        dl_service (deep_lynx.DataSourcesApi): deep lynx data source api
        file_id (string): the id of a file
        container_id (str): deep lynx container id
    """
    return dl_service.retrieve_file(container_id=container_id, file_id=file_id)


def compile_data(dl_service: deep_lynx.DataQueryApi, dl_event: list = None):
    """
    Complies a dataset from deep lynx queries
    Args
        dl_service (deep_lynx.DataQueryApi): deep lynx query api
        dl_event (list): a list of json objects from a deep lynx event
    Return
        dataset (DataFrame or Series): a pandas DataFrame or Series of the data
    """
    dataset = pd.DataFrame()
    return dataset


def write_csv(dataset: pd.DataFrame or pd.Series, path: str):
    """
    Writes the dataset to .csv file
    Args
        dataset (DataFrame or Series): a pandas DataFrame or Series of the data
        path (string): the file path to write the data to e.g. data/*.csv
    """
    dataset.to_csv(path, index=False)


def deep_lynx_init():
    """ 
    Returns the container id, data source id, and api client for use with the DeepLynx SDK.
    Assumes token authentication. 

    Args
        None
    Return
        container_id (str), data_source_id (str), api_client (ApiClient)
    """
    # initialize an ApiClient for use with deep_lynx APIs
    configuration = deep_lynx.configuration.Configuration()
    configuration.host = os.getenv('DEEP_LYNX_URL')
    api_client = deep_lynx.ApiClient(configuration)

    # authenticate via an API key and secret
    auth_api = deep_lynx.AuthenticationApi(api_client)
    token = auth_api.retrieve_o_auth_token(x_api_key=os.getenv('DEEP_LYNX_API_KEY'),
        x_api_secret=os.getenv('DEEP_LYNX_API_SECRET'), x_api_expiry='12h')

    # update header
    api_client.set_default_header('Authorization', 'Bearer {}'.format(token))
    
    # get container ID
    container_id = None
    container_api = deep_lynx.ContainersApi(api_client)
    containers = container_api.list_containers()
    for container in containers.value:
        if container.name == os.getenv('CONTAINER_NAME'):
            container_id = container.id
            continue

    if container_id is None:
        print('Container not found')
        return None, None, None

    # get data source ID, create if necessary
    data_source_id = None
    datasources_api = deep_lynx.DataSourcesApi(api_client)

    datasources = datasources_api.list_data_sources(container_id)
    for datasource in datasources.value:
        if datasource.name == os.getenv('DATA_SOURCE_NAME'):
            data_source_id = datasource.id
    if data_source_id is None:
        datasource = datasources_api.create_data_source(deep_lynx.models.create_data_source_request.CreateDataSourceRequest(
            os.getenv('DATA_SOURCE_NAME'), 'standard', True
        ), container_id)
        data_source_id = datasource.value.id

    return container_id, data_source_id, api_client
