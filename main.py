from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# # If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def main():
    email_addresses = ["rydercatonio8@gmail.com","catonio@ualberta.ca"]


    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
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

        for person in email_addresses:
            test = "from:" + person + " " + "is:unread"
            messages = service.users().messages().list(userId="me",labelIds=['INBOX'],q=test).execute()
            for message in messages['messages']:
                msg = service.users().messages().get(userId="me",id=message['id']).execute()
                print(msg['snippet'])











        # print(messages)

        # for message in messages:
        #     print(message)
        # #     # print(message['id'])
        # #     # msg = service.users().messages().get(userId="me",id=message['id']).execute()
        # #     # email_body = msg['payload']
        # #     # print(email_body)



        # print(messages)
        # msg = messages['messages']

        # for m in msg:
        #     print(m['snippet'])




        # print(msg)






        # message = service.users().messages().get(userId="me",id="185a396e381b07ad",format="raw").execute()


        # print(messages['snippet'])
        # print(results)



        # results = service.users().messages().list(userId="me",labelIds=['INBOX'],q="is:unread").execute()
        # messages= results.get('messages',[])
        # print(messages)
        # # results = service.users().labels().list(userId='me').execute()
        # # labels = results.get('labels', [])


    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()