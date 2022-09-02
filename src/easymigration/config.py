import os
from os.path import exists
import yaml
from pkgutil import get_data
from logging import config as logconfig
import logging

configuration_file = '.easy-migration-tools.yml'
example_configuration_file = 'example-easy-migration-tools.yml'
configuration_file_locations = [configuration_file, os.path.expanduser('~/' + configuration_file)]


def ensure_configuration_file_exists():
    config = find_config_file()
    if config is None:
        print("No %s found; instantiating in current directory" % configuration_file)
        with open(configuration_file, 'wb') as f:
            example_cfg = get_data('easymigration', example_configuration_file)
            if example_cfg is None:
                print("WARN: cannot find example-easy-migration-tools.yml")
            else:
                f.write(example_cfg)


def find_config_file():
    return next(filter(lambda p: exists(p), configuration_file_locations), None)


def init():
    """
    Initialization function to run by each script. It reads `.easy-migration-tools.yml`, searching the current
    working directory and then the user's home directory. If `.easy-migration-tools.yml` does not exist yet,
    then it is first instantiated in the current working directory, from `example-easy-migration-tools.yml`.

    This function then proceeds to read the configuration into a dictionary, initialize the logging framework with the
    settings found under the `logging` key and return the complete dictionary to the caller.

    Returns:
        a dictionary with the configuration settings
    """
    ensure_configuration_file_exists()
    with open(find_config_file(), 'r') as stream:
        config = yaml.safe_load(stream)
        logconfig.dictConfig(config['logging'])
        logging.debug("Initialized logging")
        return config
