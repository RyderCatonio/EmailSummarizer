from __future__ import print_function

import os.path
import base64
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth
import datetime
from email.mime.text import MIMEText


from email.message import EmailMessage

# # If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.compose']


def main():
    # Read in emails from textfile
    email_addresses = []
    with open('emails.txt') as f:
        email_addresses = f.read().splitlines()
    f.close()

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:

            token.write(creds.to_json())
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        email = '<h2><strong>Email Summary</strong></h2>'
        for person in email_addresses:  # Iterate through emails from text file
            email += "<h3><strong>From:</strong> " + person + "<br></h3>"
            query = "from:" + person + " " + "is:unread"
            messages = service.users().messages().list(
                userId="me", labelIds=['INBOX'], q=query).execute()  # Get unread emails for the specified email address
            try:
                for message in messages['messages']:  # Find the message body
                    msg = service.users().messages().get(
                        userId="me", id=message['id']).execute()
                    date_time = str(datetime.datetime.fromtimestamp(
                        (int(msg['internalDate'])/1000)))
                    subject = "None"
                    email += "<strong>Sent @ " + \
                        date_time + "<br></strong>"
                    if "payload" in msg and "headers" in msg["payload"]:
                        for header in msg["payload"]["headers"]:
                            if header["name"] == "Subject":
                                subject = header["value"]
                                email += "<strong>Subject:</strong> " + subject + "<br>"
                                break
                    if "parts" in msg.get("payload"):
                        for part in msg["payload"]["parts"]:
                            if part["mimeType"] == "text/html":
                                if "data" in part["body"]:
                                    message_body = base64.urlsafe_b64decode(
                                        part["body"]["data"].encode("ASCII")).decode("utf-8")
                                    soup = BeautifulSoup(
                                        message_body, "html.parser")
                                    email += soup.get_text(separator='\n') + \
                                        "<br><br>"

                email += "<br><br>"  # Split each recipient with space

            except:  # If no messages
                email += "You have no unread messages from this email address"

        # Send message with summary
        message = MIMEText(email, 'html')
        message['to'] = 'rcatonio@ualberta.ca'
        message['subject'] = 'Email Summary'
        create_message = {'raw': base64.urlsafe_b64encode(
            message.as_bytes()).decode()}
        service.users().messages().send(
            userId="me", body=create_message).execute()

    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
