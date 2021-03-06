#!/usr/bin/env python3

import getopt
import logging
import os
import pprint
import pymysql.cursors
import sys
import yaml

from database_drivers.MysqlDriver import MysqlDriver
from parsers.Parser import parse_activity_to_row, parse_row
from utils.config import load_config

from datetime import date, timedelta

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

DEFAULT_ACTIVITY_TABLE = 'garmin_activities'
DEFAULT_DAILY_STATS_TABLE = 'garmin_daily_stats'

pp = pprint.PrettyPrinter(indent=4)

config = load_config()

if 'garmin_users' not in config:
    print('No users specified')
    sys.exit(1)

if 'databases' not in config:
    print('No databases specified')
    sys.exit(1)

activity_data = []
splits_data = []
sets_data = []
daily_stats_data = []

for user in config['garmin_users']:
    client = Garmin(user['username'], user['password'])
    client.login()
    print('Connected to Garmin successfully!')

    # Activity retrieval
    strategy = config['activity_config'].get('retrieval_strategy', 'by_limit')
    if strategy == 'by_limit':
        activities = client.get_activities(config['activity_config'].get('start', 0), config['activity_config'].get('limit', 2))
    elif strategy == 'by_date':
        end = date.today()
        start = end - timedelta(days = config['activity_config'].get('limit', 2))
        activities = client.get_activities_by_date(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    else:
        print(f'Unknown retrieval strategy for activities: {strategy}')

    for activity in activities:
        if activity['activityType']['typeKey'] in config['activity_config']['types']:
            activity_data.append(parse_activity_to_row(activity, config['activity_config'], user['username']))

    # Daily stat retrieval
    strategy = config['daily_stats_config'].get('retrieval_strategy', 'by_limit')
    if strategy == 'by_limit':
        day = date.today()
        for i in range(config['daily_stats_config'].get('limit', 5)):
            day = date.today() - timedelta(days = i)
            print(f'Gathering daily stats for {day}')
            daily_stats_data.append(parse_row(client.get_stats(day.strftime('%Y-%m-%d')), config['daily_stats_config'], user['username']))
    else:
        print(f'Unknown retrieval strategy for daily stats: {strategy}')

pp.pprint(activity_data)
pp.pprint(daily_stats_data)

config['activity_config']['fields']['user'] = {'db_col_type': 'VARCHAR(128)'}
config['activity_config']['fields']['activityType'] = {'db_col_type': 'VARCHAR(32)'}

for db_config in config['databases']:
    if db_config['type'] == 'mysql':
        driver = MysqlDriver(db_config, config)

    driver.insert_data(activity_data, config['activity_config'].get('table', DEFAULT_ACTIVITY_TABLE))
    driver.insert_data(daily_stats_data, config['daily_stats_config'].get('table', DEFAULT_DAILY_STATS_TABLE))

