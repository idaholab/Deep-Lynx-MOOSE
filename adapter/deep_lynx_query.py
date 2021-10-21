# Copyright 2021, Battelle Energy Alliance, LLC

import os
import json
import settings
import pandas as pd
import deep_lynx


def deep_lynx_query(dl_service: deep_lynx.DeepLynxService, data_file: str):
    """
    Queries deep lynx for data and writes the dataset to .csv file
    Args
        dl_service (DeepLynxService): deep lynx service object
        data_file (str): location of the file to write
    """
    dataset = compile_data(dl_service)
    write_csv(dataset, data_file)


def query(dl_service: deep_lynx.DeepLynxService, payload: str):
    """
    Queries Deep Lynx for nodes or edges
    Args
        dl_service (DeepLynxService): deep lynx service object
        payload (string): the graphQL query
    Return 
        data (dictionary): a dictionary of nodes or edges
        
    """
    data = dl_service.query(dl_service.container_id, payload)
    return data


def download_file(dl_service: deep_lynx.DeepLynxService, file_id: str):
    """
    Downloads a file from Deep Lynx
    Args
        dl_service (DeepLynxService): deep lynx service object
        file_id (string): the id of a file
    """
    return dl_service.download_file(dl_service.container_id, file_id)


def retrieve_file(dl_service: deep_lynx.DeepLynxService, file_id: str):
    """
    Retrieves a file from Deep Lynx
    Args
        dl_service (DeepLynxService): deep lynx service object
        file_id (string): the id of a file
    """
    return dl_service.retrieve_file(dl_service.container_id, file_id)


def compile_data(dl_service: deep_lynx.DeepLynxService):
    """
    Complies a dataset from deep lynx queries
    Args
        dl_service (DeepLynxService): deep lynx service object
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
