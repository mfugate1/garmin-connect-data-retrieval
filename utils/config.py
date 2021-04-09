import os
import sys
import yaml

def load_config():
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        if os.path.exists('config.yaml'):
            config_file = 'config.yaml'
        else:
            config_file = None

    if config_file is None:
        print('No config file specified and default config.yaml not found')
        sys.exit(1)
    else:
        with open(config_file, 'r') as file:
            config = yaml.load(file, Loader=yaml.SafeLoader)
    return config