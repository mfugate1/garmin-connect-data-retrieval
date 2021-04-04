#!/usr/bin/env python3

import getopt
import logging
import os
import pprint
import pymysql.cursors
import sys
import yaml

from MysqlDriver import MysqlDriver

from datetime import date, timedelta

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

pp = pprint.PrettyPrinter(indent=4)

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

if 'garmin_users' not in config:
    print('No users specified')
    sys.exit(1)

if 'databases' not in config:
    print('No databases specified')
    sys.exit(1)

activity_data = []
splits_data = []
sets_data = []

for user in config['garmin_users']:
    client = Garmin(user['username'], user['password'])
    client.login()
    print('Connected to Garmin successfully!')

    if 'limit' in config:
        activities = client.get_activities(config.get('start', 0), config['limit'])
    elif 'from_days_ago' in config:
        end = date.today()
        start = end - timedelta(days = config['from_days_ago'])
        activities = client.get_activities_by_date(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    else:
        print('Missing one of these config options: limit, from_days_ago')
        sys.exit(1)

    for activity in activities:
        if activity['activityType']['typeKey'] in config['activities']:
            ad = {'activityType': activity['activityType']['typeKey'], 'user': user['username']}
            for key, value in activity.items():
                if key in config['fields']:
                    k = key
                    v = value
                    if config['fields'][key] is not None and 'units' in config['fields'][key]:
                        k = f"{key}_{config['fields'][key]['units'].replace(' ', '_')}"
                    if config['fields'][key] is not None and value is not None and 'transform' in config['fields'][key]:
                        pp.pprint('Transforming {}: [{}] with value {}'.format(key, config['fields'][key]['transform'], value))
                        try:
                            v = eval(config['fields'][key]['transform'])
                        except ZeroDivisionError as ex:
                            print('WARNING - Divide by zero error when transforming {}. Value will remain as {}'.format(key, value))
                    ad[k] = v
            activity_data.append(ad)

config['fields']['user'] = {'db_col_type': 'VARCHAR(128)'}
config['fields']['activityType'] = {'db_col_type': 'VARCHAR(32)'}

for db_config in config['databases']:
    if db_config['type'] == 'mysql':
        driver = MysqlDriver(db_config, config)

    driver.insert_data(activity_data)

