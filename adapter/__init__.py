# Copyright 2021, Battelle Energy Alliance, LLC
import os
import logging
import json
import time
import datetime
from flask import Flask, request, Response, json

import deep_lynx
from . import moose_adapter
from . import settings

# configure logging. to overwrite the log file for each run, add option: filemode='w'
logging.basicConfig(filename='MOOSEAdapter.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w',
                    datefmt='%m/%d/%Y %H:%M:%S')

print('Application started. Logging to file MOOSEAdapter.log')

data_ingested_adapters = json.loads(os.getenv("DATA_SOURCES"))["Data Sources"]


def create_app():
    """ This file and aplication is the entry point for the `flask run` command """
    app = Flask(os.getenv('FLASK_APP'), instance_relative_config=True)

    existEnvFile = False
    inputFileName = False
    configFileName = False
    runFileName = False
    outputFileName = False
    pythonPath = False
    mooseOptPath = False
    deepLynxUrl = False
    containerName = False
    dataSourceName = False

    if os.path.isfile('.env'):
        existEnvFile = True
    else:
        logging.error('Fail: Create .env file using .env_sample as a guide.')

    if os.getenv('DEEP_LYNX_URL') is not None:
        deepLynxUrl = True
    else:
        logging.error('Fail: Provide an "DEEP_LYNX_URL" variable in the .env file')

    if os.getenv('CONTAINER_NAME') is not None:
        containerName = True
    else:
        logging.error('Fail: Provide an "CONTAINER_NAME" variable in the .env file')

    if os.getenv('DATA_SOURCE_NAME') is not None:
        dataSourceName = True
    else:
        logging.error('Fail: Provide an "DATA_SOURCE_NAME" variable in the .env file')

    if existEnvFile and deepLynxUrl and containerName and dataSourceName:
        # instantiate deep_lynx_service
        dlService = deep_lynx.DeepLynxService(os.getenv('DEEP_LYNX_URL'), os.getenv('CONTAINER_NAME'),
                                    os.getenv('DATA_SOURCE_NAME'))
        dlService.init()
    else:
        print('Setup Error: Check logging file MOOSEAdapter.log for more information')

    # config available via os.getenv('VAR_NAME')

    @app.route('/events', methods=['POST'])
    def events():
        if request.method == 'POST':
            if 'application/json' not in request.content_type:
                return Response('Unsupported Content Type. Please use application/json', status=400)
            data = request.get_json()

            logging.info('Received event with data: ' + json.dumps(data))
            import_data = dlService.list_import_data(dlService.container_id, data['import_id'])

            # parse event data and run dt_driver main
            # check for event object type
            try:
                dl_event = import_data['value'][0]['data']

                if 'instruction' in dl_event:
                    if dl_event['instruction'] == 'run':
                        logging.info('New run event')
                        print('New run event')

                        # if event object type with instruction 'run' is found,
                        # grab original data id or import id and query DL for reactor map data
                        event_data = dlService.list_import_data(dlService.container_id, dl_event['importID'])

                        if 'value' not in event_data:
                            return Response(response=json.dumps({'received': True}),
                                            status=200,
                                            mimetype='application/json')

                        moose_data = event_data['value'][0]['data']

                        # parse returned data and send to moose_adapter
                        # TODO: ensure incoming objects are of the format {node, parameter, value}

                        # update event object and return to Deep Lynx
                        dl_event['status'] = 'in progress'
                        dl_event['received'] = True
                        dl_event['modifiedDate'] = datetime.datetime.now().isoformat()
                        dl_event['modifiedUser'] = os.getenv('DATA_SOURCE_NAME')
                        dlService.create_manual_import(dlService.container_id, dlService.data_source_id, dl_event)

                        moose_adapter.main(moose_data, dl_event, dlService)

                        return Response(response=json.dumps(dl_event), status=200, mimetype='application/json')

            except KeyError:
                # The incoming payload doesn't have what we need, but still return a 200
                return Response(response=json.dumps({'received': True}), status=200, mimetype='application/json')

    # disable running the code twice upon start in development
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if existEnvFile and inputFileName and configFileName and runFileName and outputFileName and pythonPath and mooseOptPath and deepLynxUrl and containerName and dataSourceName:
            from . import template_parser
            createConfigFile = template_parser.main()
            if not createConfigFile:
                logging.error('Unable to create config file')

            # TODO: Uncomment/comment when data source is available, the timer disables dev reloads
            moose_adapter.main()
            # register_for_event(dlService)

    return app


def register_for_event(dlService: deep_lynx.DeepLynxService, iterations=30):
    """ Register with Deep Lynx to receive data_ingested events on applicable data sources """
    registered = False

    # List of adapters to receive events from
    data_ingested_adapters = json.loads(os.getenv("DATA_SOURCES"))["Data Sources"]

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
                        "type":
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
