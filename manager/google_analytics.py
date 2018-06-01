import argparse
import datetime
from googleapiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
CLIENT_SECRETS_PATH = 'manager/client_secrets.json' # Path to client_secrets.json file.
VIEW_ID = '113626987' #view ID of Hook Coffee's 'All Web Site Data'


def initialize_analyticsreporting():
    """Initializes the analyticsreporting service object.

    Returns:
      analytics an authorized analyticsreporting service object.
    """
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])
    flags = parser.parse_args([])

    # Set up a Flow object to be used if we need to authenticate.
    flow = client.flow_from_clientsecrets(
        CLIENT_SECRETS_PATH, scope=SCOPES,
        message=tools.message_if_missing(CLIENT_SECRETS_PATH))

    # Prepare credentials, and authorize HTTP object with them.
    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # credentials will get written back to a file.
    storage = file.Storage('analyticsreporting.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = credentials.authorize(http=httplib2.Http())

    # Build the service object.
    analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

    return analytics

def get_report_users(analytics, start_date, end_date):
    #convert date from DD-MM-YYYY to YYYY-MM-DD
    start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y").strftime("%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y").strftime("%Y-%m-%d")

    # Use the Analytics Service Object to query the Analytics Reporting API V4.
    response = analytics.reports().batchGet(
        body={
            'reportRequests': [
                {
                    'viewId': VIEW_ID,
                    'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
                    'metrics': [{'expression': 'ga:users'}]
                }]
        }
    ).execute()

    return response['reports'][0]['data']['rows'][0]['metrics'][0]['values'][0]


# def print_response(response):
#     """Parses and prints the Analytics Reporting API V4 response"""
#
#     for report in response.get('reports', []):
#         columnHeader = report.get('columnHeader', {})
#         dimensionHeaders = columnHeader.get('dimensions', [])
#         metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
#         rows = report.get('data', {}).get('rows', [])
#
#         for row in rows:
#             dimensions = row.get('dimensions', [])
#             dateRangeValues = row.get('metrics', [])
#
#             for header, dimension in zip(dimensionHeaders, dimensions):
#                 print header + ': ' + dimension
#
#             for i, values in enumerate(dateRangeValues):
#                 print 'Date range (' + str(i) + ')'
#                 for metricHeader, value in zip(metricHeaders, values.get('values')):
#                     print metricHeader.get('name') + ': ' + value
#

# def main():
#
#     analytics = initialize_analyticsreporting()
#     response = get_report(analytics)
#     print_response(response)
#
# if __name__ == '__main__':
#     main()