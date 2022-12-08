# MOOSE Adapter changelog

The latest version of this file can be found at the master branch of the MOOSE-Adapter repository.

# 0.0.3 (2021-11-16)
## Added
* Added tests for `edit_input_file.py`
* Added example files to the `data` directory
* Added `utils` directory that validates the extension and whether the path exists

## Fixed
* Fixed tests for the `moose_adapter.py` and `template_parser.py`

## Changed
* Moved changing a MOOSE input file to separate file called `edit_input_file.py`
* Changed validation of environment variables to use the `environs` package

# 0.0.2 (2021-10-21)
## Added

* Added querying Deep Lynx for data in `deep_lynx_query.py`
* Added importing the data to Deep Lynx in `deep_lynx_import.py`


# 0.0.1 (2021-08-12)
## Added
* Added initial files to repository
