# garmin-connect-data-retrieval
A script to retrieve data from garmin connect and load it into a database

Requires https://pypi.org/project/garminconnect/ to be installed wherever the script is run

`pip install garminconnect`

To run the script:

`./garmin-connect-retrieval.py`

I use the included Dockerfile as a jenkins worker to periodically run this script, but it could also be used as a standalone container to run the script

Supported databases:
- MySQL/MariaDB

# Challenge scraper
Script to get challenges directly from the garmin connect website (since the API doesn't seem to give any way to retrieve them)
Requires selenium
`./challenge-scraper.py`

Upcoming features:
- Support for gathering splits/sets from activities
- Support for gathering all missing activities, not just the latest ones
- If you have a request for a database to support, open an issue and I'll see what I can do