# garmin-connect-data-retrieval
A script to retrieve data from garmin connect and load it into a database

Requires https://pypi.org/project/garminconnect/ to be installed wherever the script is run

`pip install garminconnect`

To run the script:

`./garmin-connect-retrieval.py`

I use the included Dockerfile as a jenkins worker to periodically run this script, but it could also be used as a standalone container to run the script

Supported databases:
- MySQL/MariaDB

Upcoming features:
- Support for gathering splits/sets from activities
- Support for gathering all missing activities, not just the latest ones
- Support for updating an activity that has changed since it was retrieved (currently just ignores that row)
- If you have a request for a database to support, open an issue and I'll see what I can do