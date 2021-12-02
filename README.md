# MOOSE Adapter

This project is an adapter that utilizes the Deep Lynx event system. After this application registers for events, received events will be parsed for updates to a template `.i` MOOSE input file. The updated input file will then be run, creating an output `.json` file. This file is sent to [Deep Lynx](https://github.com/idaholab/Deep-Lynx) for ingestion.  

To run this code, first copy the `.env_sample` file and rename it to `.env`. Several parameters must be present:
* DEEP_LYNX_URL: The base URL at which calls to Deep Lynx should be sent
* CONTAINER_NAME: The container name within Deep Lynx
* DATA_SOURCE_NAME: A name for this data source to be registered with Deep Lynx
* PYTHONPATH: The path to the local MOOSE python folder
* CONFIG_INPUT_FILE_NAME: The `.i` template input filename to look for
* CONFIG_FILE_NAME: The `.cfg` configuration filename to look for
* RUN_FILE_NAME: The `.i` input filename to run in MOOSE
* MOOSE_OPT_PATH: The path to the local MOOSE executable


Logs will be written to a logfile, stored in the root directory of the project. The log filename is set in `main()` of `moose_adapter.py`.

## Getting Started
* Complete the [Poetry installation](https://python-poetry.org/) 
* All following commands are run in the root directory of the project:
    * Run `poetry install` to install the defined dependencies for the project.
    * Run `poetry shell` to spawns a shell.
    * Finally, run the project with the command `flask run`

## MOOSE Installation
* Complete the [MOOSE installation](https://mooseframework.inl.gov/getting_started/installation/)
* Complete the [setup](https://mooseframework.inl.gov/python/index.html) for the MOOSE Python Tools
    * Add `export PYTHONPATH=$PYTHONPATH:~/projects/moose/python` to your bash environment

## MOOSE Dependencies
The MOOSE Adapter uses the `pyhit` and `moosetree` modules within MOOSE. For more information, visit the `Helpful Links` section.

## Contributing

This project uses [yapf](https://github.com/google/yapf) for formatting. Please install it and apply formatting before submitting changes (e.g. `yapf --in-place --recursive . --style={column_limit:120}`)

## Helpful Links
* MOOSE Code
    * [pyhit](https://github.com/idaholab/moose/blob/next/python/pyhit/pyhit.py)
    * [moosetree](https://github.com/idaholab/moose/tree/next/python/moosetree)
* User Guides
    * [pyhit tutorial](https://mooseframework.inl.gov/python/pyhit/index.html)
    * [moosetree package](https://mooseframework.inl.gov/python/moosetree/index.html)
    * [input file syntax](https://mooseframework.inl.gov/application_usage/input_syntax.html#) shows the use of global variables in input file

## Other Software
Idaho National Laboratory is a cutting edge research facility which is a constantly producing high quality research and software. Feel free to take a look at our other software and scientific offerings at:

[Primary Technology Offerings Page](https://www.inl.gov/inl-initiatives/technology-deployment)

[Supported Open Source Software](https://github.com/idaholab)

[Raw Experiment Open Source Software](https://github.com/IdahoLabResearch)

[Unsupported Open Source Software](https://github.com/IdahoLabCuttingBoard)

## License

Copyright 2021 Battelle Energy Alliance, LLC

Licensed under the LICENSE TYPE (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  https://opensource.org/licenses/MIT  

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.



Licensing
-----
This software is licensed under the terms you may find in the file named "LICENSE" in this directory.


Developers
-----
By contributing to this software project, you are agreeing to the following terms and conditions for your contributions:

You agree your contributions are submitted under the MIT license. You represent you are authorized to make the contributions and grant the license. If your employer has rights to intellectual property that includes your contributions, you represent that you have received permission to make contributions and grant the required license on behalf of that employer.