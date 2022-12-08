# Copyright 2021, Battelle Energy Alliance, LLC

# Python Packages
import os
import logging
import json
import time
from flask import Flask, request, Response, json
import environs
import deep_lynx
import threading

# Repository Modules
from .moose_adapter import main
from .deep_lynx_query import query_deep_lynx
import utils
import settings

# Global variables
api_client = None
lock_ = threading.Lock()
threads = list()
number_of_events = 1
env = environs.Env()
new_data = False

# configure logging. to overwrite the log file for each run, add option: filemode='w'
logging.basicConfig(filename='MOOSEAdapter.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w',
                    datefmt='%m/%d/%Y %H:%M:%S')

print('Application started. Logging to file MOOSEAdapter.log')

# configure logging. to overwrite the log file for each run, add option: filemode='w'
logging.basicConfig(filename='MOOSEAdapter.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w',
                    datefmt='%m/%d/%Y %H:%M:%S')

print('Application started. Logging to file MOOSEAdapter.log')


def create_app():
    """ This file and aplication is the entry point for the `flask run` command """
    global env
    global new_data
    #import pdb; pdb.set_trace()
    app = Flask(os.getenv('FLASK_APP'), instance_relative_config=True)

    # Validate .env file exists
    utils.validate_paths_exist(".env")

    # Check required variables in the .env file, and raise error if not set
    env.read_env()
    env.url("DEEP_LYNX_URL")
    env.str("CONTAINER_NAME")
    env.str("DATA_SOURCE_NAME")
    env.list("DATA_SOURCES")
    env.path("PYTHONPATH")
    env.path("MOOSE_OPT_PATH")
    env.path("CONFIG_FILE_NAME")
    env.path("RUN_FILE_NAME")
    env.int("IMPORT_FILE_WAIT_SECONDS")
    env.int("REGISTER_WAIT_SECONDS")

    # Purpose to run flask once (not twice)
    # Purpose to run flask once (not twice)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Instantiate deep_lynx
        container_id, data_source_id, api_client = deep_lynx_init()
        os.environ["CONTAINER_ID"] = container_id
        os.environ["DATA_SOURCE_ID"] = data_source_id

        # Register for events to listen for
        register_for_event(api_client)

        # Create Thread object that runs the machine learning algorithms
        # Thread object: activity that is run in a separate thread of control
        # Daemon: a process that runs in the background. A daemon thread will shut down immediately when the program exits.
        moose_thread = threading.Thread(target=main, daemon=True, name="moose_thread")
        print("Created moose_thread")
        threads.append(moose_thread)
        # Start the thread’s activity
        new_data = True
        moose_thread.start()

    @app.route('/moose', methods=['POST'])
    def events():
        global number_of_events
        global lock_
        global new_data
        if 'application/json' not in request.content_type:
            logging.warning('Received /events request with unsupported content type')
            return Response('Unsupported Content Type. Please use application/json', status=400)

        # Data from graph has been received
        data = request.get_json()
        try:
            file_id = data["query"]["fileID"]
            logging.info('Received event with data: ' + json.dumps(data))
        except KeyError:
            # The incoming payload doesn't have what we need, but still return a 200
            return Response(response=json.dumps({'received': True}), status=200, mimetype='application/json')

        # Retrieves file from Deep Lynx
        event_name = "event_thread_" + str(number_of_events)
        # Thread object: activity that is run in a separate thread of control
        event_thread = threading.Thread(target=query_deep_lynx, args=(file_id, ), name=event_name)
        print("Created ", event_name)
        threads.append(event_thread)
        number_of_events += 1
        # Start the thread’s activity
        event_thread.start()
        # Join: Wait until the thread terminates. This blocks the calling thread until the thread whose join() method is called terminates.
        event_thread.join()
        print(event_name, " is done")
        with lock_:
            new_data = True
        return Response(response=json.dumps({'received': True}), status=200, mimetype='application/json')

    return app


def register_for_event(api_client: deep_lynx.ApiClient, iterations=30):
    """
    Register with Deep Lynx to receive data_ingested events on applicable data sources
    
    Args
        api_client (deep_lynx.ApiClient): deep lynx api client
        iterations (integer): the number of interations to try registering for events
    """
    registered = False
    # List of adapters to receive events from
    data_ingested_adapters = json.loads(os.getenv("DATA_SOURCES"))

    # Register events for listening from other data sources
    while registered == False and iterations > 0:
        # Get a list of data sources and validate that no error occurred
        datasource_api = deep_lynx.DataSourcesApi(api_client)
        data_sources = datasource_api.list_data_sources(os.getenv("CONTAINER_ID"))

        if data_sources.is_error == False and len(data_sources.value) > 0:
            #data_sources = data_sources.to_dict()["value"]
            for data_source in data_sources.value:
                # If the data source is found, create a registered event
                if data_source.name in data_ingested_adapters:

                    events_api = deep_lynx.EventsApi(api_client)

                    # verify that this event action does not already exist
                    # by comparing to the established event action we would like to create

                    event_action = deep_lynx.CreateEventActionRequest(
                        data_source.container_id, data_source.id, "file_created", "send_data", None,
                        "http://" + os.getenv('FLASK_RUN_HOST') + ":" + os.getenv('FLASK_RUN_PORT') + "/moose",
                        os.getenv("DATA_SOURCE_ID"), True)

                    actions = events_api.list_event_actions()
                    for action in actions.value:

                        # if destination, event_type, and data_source_id match, we know that this
                        # event action already exists
                        if action.destination == event_action.destination and action.event_type == event_action.event_type \
                            and action.data_source_id == event_action.data_source_id:
                            # this exact event action already exists, remove data source from list
                            logging.info('Event action on ' + data_source.name + ' already exists')
                            data_ingested_adapters.remove(data_source.name)

                    # continue event action creation if the same was not already found
                    if data_source.name in data_ingested_adapters:
                        create_action_result = events_api.create_event_action(event_action)

                        if create_action_result.is_error:
                            logging.warning('Error creating event action: ' + create_action_result.error)
                        else:
                            logging.info('Successful creation of event action on ' + data_source.name + ' datasource')
                            data_ingested_adapters.remove(data_source.name)

                    # If all events are registered
                    if len(data_ingested_adapters) == 0:
                        registered = True
                        logging.info('Successful registration on all adapters')
                        return registered

        # If the desired data source and container is not found, repeat
        logging.info(
            f'Datasource(s) {", ".join(data_ingested_adapters)} not found. Next event registration attempt in {os.getenv("REGISTER_WAIT_SECONDS")} seconds.'
        )
        time.sleep(float(os.getenv('REGISTER_WAIT_SECONDS')))
        iterations -= 1

    return registered


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

    # perform API token authentication only if values are provided
    if os.getenv('DEEP_LYNX_API_KEY') != '' and os.getenv('DEEP_LYNX_API_KEY') is not None:

        # authenticate via an API key and secret
        auth_api = deep_lynx.AuthenticationApi(api_client)

        try:
            token = auth_api.retrieve_o_auth_token(x_api_key=os.getenv('DEEP_LYNX_API_KEY'),
                                                   x_api_secret=os.getenv('DEEP_LYNX_API_SECRET'),
                                                   x_api_expiry='12h')
        except TypeError:
            print("ERROR: Cannot connect to DeepLynx.")
            logging.error("Cannot connect to DeepLynx.")
            return '', '', None

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
        datasource = datasources_api.create_data_source(
            deep_lynx.CreateDataSourceRequest(os.getenv('DATA_SOURCE_NAME'), 'standard', True), container_id)
        data_source_id = datasource.value.id

    return container_id, data_source_id, api_client
