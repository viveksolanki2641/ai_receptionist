import datetime
import os
import pickle
import pytz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
CALANDER_CREDENTIALS_PATH= os.getenv("CALANDER_CREDENTIALS_PATH")
# Define the required Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """
    Authenticate and return the Google Calendar service.

    This function handles authentication by checking if a valid 
    token exists in the 'token.pickle' file. If no valid token is found,
    it prompts the user to authenticate through a browser and saves the
    credentials for future use.
    
    Returns:
        service (Resource): The authenticated Google Calendar API service.
    """
    
    creds = None
    
    # Check if token.pickle exists and load credentials from it
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no credentials are found or they are invalid, authenticate again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired credentials
            creds.refresh(Request())
        else:
            # Prompt the user for authentication if no valid token is found
            flow = InstalledAppFlow.from_client_secrets_file(CALANDER_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use in 'token.pickle'
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    # Return the authenticated Google Calendar API service
    return build('calendar', 'v3', credentials=creds)


def convert_ist_to_utc(ist_time_str, date):
    """
    Convert IST (Indian Standard Time) datetime to UTC (Coordinated Universal Time).

    Args:
        ist_time_str (str): The time in IST (HH:MM:SS format).
        date (str): The date (YYYY-MM-DD format).
    
    Returns:
        datetime: The equivalent UTC datetime.
    """
    
    # Define the IST timezone
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    # Convert the date and time string to a naive datetime object
    naive_ist_datetime = datetime.datetime.strptime(f"{date} {ist_time_str}", "%Y-%m-%d %H:%M:%S")
    
    # Localize the naive datetime (convert it to IST)
    localized_ist_datetime = ist_tz.localize(naive_ist_datetime)
    
    # Convert the localized IST time to UTC time
    utc_datetime = localized_ist_datetime.astimezone(pytz.utc)
    
    return utc_datetime


def check_existing_meetings(service, date, time):
    """
    Check for existing meetings at the given date and time in IST.

    Args:
        service (Resource): The authenticated Google Calendar API service.
        date (str): The date to check for existing meetings (YYYY-MM-DD).
        time (str): The time to check for existing meetings (HH:MM:SS).

    Returns:
        list: A list of events found at the specified time.
    """
    
    # Define the start and end datetime for the meeting
    start_datetime = f"{date}T{time}+00:00"
    end_datetime = (datetime.datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S+00:00") + 
                    datetime.timedelta(hours=1)).isoformat() + "Z"
    
    # Query the Google Calendar API for events between the start and end times
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_datetime,
        timeMax=end_datetime,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    # Return the list of events found
    return events_result.get('items', [])


def schedule_meeting(service, user_name, user_email, service_name, date, time_ist):
    """
    Schedule a meeting in Google Calendar with the user's email in IST.

    Args:
        service (Resource): The authenticated Google Calendar API service.
        user_name (str): The name of the user to schedule the meeting with.
        user_email (str): The email address of the user to send the invitation.
        service_name (str): The name of the service for the meeting.
        date (str): The date of the meeting (YYYY-MM-DD).
        time_ist (str): The start time of the meeting in IST (HH:MM:SS).

    Returns:
        str: The link to the scheduled event in the Google Calendar.
    """
    
    # Convert the given IST time to UTC time
    start_utc = convert_ist_to_utc(time_ist, date)
    
    # Calculate the end time (1 hour after the start time)
    end_utc = start_utc + datetime.timedelta(hours=1)
    
    # Prepare the event details to be added to the calendar
    event = {
        'summary': f"Appointment with {user_name} for {service_name}",
        'start': {'dateTime': start_utc.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_utc.isoformat(), 'timeZone': 'UTC'},
        'attendees': [{'email': user_email}],
    }
    
    # Insert the event into the Google Calendar
    event = service.events().insert(calendarId='primary', body=event).execute()
    
    # Return the link to the scheduled event
    return event.get('htmlLink')
