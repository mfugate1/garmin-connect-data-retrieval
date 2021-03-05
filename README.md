# garmin-connect-data-retrieval
A script to retrieve data from garmin connect and load it into a database

Requires https://pypi.org/project/garminconnect/ to be installed wherever the script is run

`pip install garminconnect`

To run the script:

`./garmin-connect-retrieval.py`

If there is an issue while communicating with Garmin Connect, it will print an error message and return an exit code based on the exception that was caught

I use the included Dockerfile as a jenkins worker to periodically run this script, but it could also be used as a standalone container to run the script

