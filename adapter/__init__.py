# Copyright 2021, Battelle Energy Alliance, LLC
import os
import logging
import json
import time
import datetime
from flask import Flask, request, Response, json
import environs
import deep_lynx

from . import moose_adapter
import utils
import settings

# configure logging. to overwrite the log file for each run, add option: filemode='w'
logging.basicConfig(filename='MOOSEAdapter.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w',
                    datefmt='%m/%d/%Y %H:%M:%S')

print('Application started. Logging to file MOOSEAdapter.log')


def create_app():
    """ This file and aplication is the entry point for the `flask run` command """
    app = Flask(os.getenv('FLASK_APP'), instance_relative_config=True)

    # Validate .env file exists
    utils.validatePathsExist(".env")

    # Check required variables in the .env file, and raise error if not set
    env = environs.Env()
    env.read_env()
    env.url("DEEP_LYNX_URL")
    env.str("CONTAINER_NAME")
    env.str("DATA_SOURCE_NAME")
    env.list("DATA_SOURCES")
    env.path("PYTHONPATH")
    env.path("MOOSE_OPT_PATH")
    env.path("QUERY_FILE_NAME")
    env.path("CONFIG_INPUT_FILE_NAME")
    env.path("CONFIG_FILE_NAME")
    env.path("RUN_FILE_NAME")
    env.path("IMPORT_FILE_NAME")
    env.int("QUERY_FILE_WAIT_SECONDS")
    env.int("IMPORT_FILE_WAIT_SECONDS")
    env.int("REGISTER_WAIT_SECONDS")

    # Instantiate deep_lynx_service
    dlService = deep_lynx.DeepLynxService(os.getenv('DEEP_LYNX_URL'), os.getenv('CONTAINER_NAME'),
                                          os.getenv('DATA_SOURCE_NAME'))
    dlService.init()

    @app.route('/events', methods=['POST'])
    def events():
        import pdb
        pdb.set_trace()
        print(request)

        if request.method == 'POST':
            if 'application/json' not in request.content_type:
                return Response('Unsupported Content Type. Please use application/json', status=400)
            data = request.get_json()

            logging.info('Received event with data: ' + json.dumps(data))
            import_data = dlService.list_import_data(dlService.container_id, data['import_id'])
            print(import_data)
            # parse event data and run dt_driver main
            # check for event object type
            try:
                dl_event = import_data['value'][0]['data']
                print(dl_event)
                if 'instruction' in dl_event:
                    if dl_event['instruction'] == 'run':
                        logging.info('New run event')
                        print('New run event')

                        # if event object type with instruction 'run' is found,
                        event_data = dlService.list_import_data(dlService.container_id, dl_event['import_id'])

                        if 'value' not in event_data:
                            return Response(response=json.dumps({'received': True}),
                                            status=200,
                                            mimetype='application/json')

                        moose_data = event_data['value'][0]['data']

                        # TODO: parse returned data and send to moose_adapter

                        # update event object and return to Deep Lynx
                        dl_event['status'] = 'in progress'
                        dl_event['received'] = True
                        dl_event['modifiedDate'] = datetime.datetime.now().isoformat()
                        dl_event['modifiedUser'] = os.getenv('DATA_SOURCE_NAME')
                        dlService.create_manual_import(dlService.container_id, dlService.data_source_id, dl_event)

                        #moose_adapter.main(moose_data, dl_event, dlService)

                        return Response(response=json.dumps(dl_event), status=200, mimetype='application/json')

            except KeyError:
                # The incoming payload doesn't have what we need, but still return a 200
                return Response(response=json.dumps({'received': True}), status=200, mimetype='application/json')

    # disable running the code twice upon start in development
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        """from . import template_parser
        createConfigFile = template_parser.main()
        if not createConfigFile:
            logging.error('Unable to create config file')"""

        # TODO: Uncomment/comment when data source is available, the timer disables dev reloads
        #moose_adapter.main()
        #register_for_event(dlService)

    return app


def register_for_event(dlService: deep_lynx.DeepLynxService, iterations=30):
    """ Register with Deep Lynx to receive data_ingested events on applicable data sources """
    registered = False

    # List of adapters to receive events from
    data_ingested_adapters = json.loads(os.getenv("DATA_SOURCES"))

    # Register events for listening from other data sources
    while not registered and iterations > 0:
        # Get a list of data sources and validate that no error occurred
        data_sources = dlService.list_data_sources(dlService.container_id)
        if data_sources['isError'] == False:
            for data_source in data_sources['value']:
                # If the data source is found, create a registered event
                if data_source['name'] in data_ingested_adapters:
                    data_source_id = data_source['id']
                    container_id = data_source['container_id']
                    dlService.create_registered_event({
                        "app_name":
                        os.getenv('DATA_SOURCE_NAME'),
                        "app_url":
                        "http://" + os.getenv('FLASK_RUN_HOST') + ":" + os.getenv('FLASK_RUN_PORT') + "/events",
                        "container_id":
                        container_id,
                        "data_source_id":
                        data_source_id,
                        "event_type":
                        "data_ingested"
                    })

                    # Verify the event was registered
                    registered_events = dlService.list_registered_events()
                    if registered_events['isError'] == False:
                        registered_events = registered_events['value']
                        if registered_events:
                            for event in registered_events:
                                if event['data_source_id'] == data_source_id and event['container_id'] == container_id:
                                    data_ingested_adapters.remove(data_source['name'])

                    # If all events are registered
                    if len(data_ingested_adapters) == 0:
                        registered = True
                        return registered

        # If the desired data source and container is not found, repeat
        logging.info(
            f'Datasource(s) {", ".join(data_ingested_adapters)} not found. Next event registration attempt in {os.getenv("REGISTER_WAIT_SECONDS")} seconds.'
        )
        time.sleep(float(os.getenv('REGISTER_WAIT_SECONDS')))
        iterations -= 1

    return registered
