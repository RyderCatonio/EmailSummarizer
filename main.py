from __future__ import print_function
import os.path
import base64
import datetime
import threading
from email.mime.text import MIMEText
from email.message import EmailMessage

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth

# # If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]


class EmailSummarizer:
    def __init__(self, send_to, subject):
        self.body = []
        self.send_to = send_to
        self.subject = subject

    # fetches relevant emails from file, emails separated by newline
    def fetch_emails(self, file_name):
        # Read in emails from textfile
        email_addresses = []
        with open(file_name, "r") as f:
            email_addresses = f.read().splitlines()

        return email_addresses


    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    def fetch_credentials(self, file_name):
        if not os.path.exists(file_name):
            return None

        return Credentials.from_authorized_user_file(file_name, SCOPES)


    # If there are no (valid) credentials available, let the user log in.
    def verify_and_login(self, creds):
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return creds



    # generates email to send(uses threads to concurrently get the data of all emails)
    def make_email(self, service, email_addresses):
        # Call the Gmail API
        emailHeader = "<h2><strong>Email Summary</strong></h2>"
        self.body = [""] * len(email_addresses)

        # threads = []
        for i, email_address in enumerate(email_addresses):  # Iterate through emails from text file
            self.make_email_body(service,email_address,i)
            # thread = threading.Thread(target=self.make_email_body, args=[service, email_address, i])
            # threads.append(thread)
            # thread.start()

        # for thread in threads:
        #     thread.join()

        return emailHeader + "".join(self.body)


    def make_email_body(self, service, email_address, idx):
        # email = "<h3><strong>From:</strong> " + email_address + "<br></h3>"
        email = ""
        query = "from:" + email_address + " " + "is:unread"
        messages = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], q=query)
            .execute()
        )  # Get unread emails for the specified email address
        try:
            email += self.make_email_message(service, messages, email_address)
        except Exception as e:  # If no messages
            email += "You have no unread messages from this email address"

        self.body[idx] = email


    # generates messages of email
    def make_email_message(self, service, messages, email_address):
        body_message = '''
                <div style="height:150px;overflow-y:auto; background-color: #dbd9d9; border-radius: 25px; padding: 20px;">
                <div style="text-align:center;">
                    <h3><strong>From: </strong>''' + email_address + '''<br></h3>
                </div>
                <table style="width:auto">
        '''



        for message in messages["messages"]:
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()
            date_time = str(
                datetime.datetime.fromtimestamp((int(msg["internalDate"]) / 1000))
            )
            subject = "None"
            body_message += "<strong>Sent @ " + date_time + "<br></strong>"
            if "payload" in msg and "headers" in msg["payload"]:
                for header in msg["payload"]["headers"]:
                    if header["name"] == "Subject":
                        subject = header["value"]
                        body_message += "<strong>Subject:</strong> " + subject + "<br>"
                        break
            payload = msg.get("payload")
            if "parts" in payload: # Check if message body resides in parts section of payload (will be found here in more complex emails with several parts to them)
                for part in payload["parts"]:
                    if part["mimeType"] == "text/html":
                        if "data" in part["body"]:
                            message_body = base64.urlsafe_b64decode(
                                part["body"]["data"].encode("ASCII")
                            ).decode("utf-8")
                            soup = BeautifulSoup(message_body, "html.parser")
                            body_message +=  "<tr><td>" + soup.get_text(separator="\n") + "</td></tr>"
            elif "body" in payload and "data" in payload["body"]: # Check if message body resides straight from payload (will be found here in simple emails with just a body)
                message_body = base64.urlsafe_b64decode(payload["body"]["data"].encode("ASCII")).decode("utf-8")
                soup = BeautifulSoup(message_body, "html.parser")
                body_message += "<tr><td>" + soup.get_text(separator="\n") + "</td></tr>"
        body_message += "</table></div>"
        body_message += "<br><br>"  # Split each recipient with space


        return body_message


    # sends the email to the client
    def send_email(self, service, body):
        message = MIMEText(body, "html")
        message["to"] = self.send_to
        message["subject"] = self.subject
        create_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
        service.users().messages().send(userId="me", body=create_message).execute()


def main():
    summarizer = EmailSummarizer("rcatonio@ualberta.ca", "Email Summary")

    # login and get proper gmail credentials
    email_addresses = summarizer.fetch_emails("emails.txt")
    creds = summarizer.fetch_credentials("token.json")
    creds = summarizer.verify_and_login(creds)

    try:
        service = build("gmail", "v1", credentials=creds)
        email = summarizer.make_email(service, email_addresses)

        # Send message with summary
        summarizer.send_email(service, email)

    except HttpError as error:
        print(f"An error occurred: {error}")




if __name__ == "__main__":
    main()
