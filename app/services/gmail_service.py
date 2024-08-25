import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the scopes required for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    def __init__(self):
        self.service = None

    def get_service(self):
        """Get or create the Gmail service."""
        if not self.service:
            self.service = self._create_gmail_service()
        return self.service

    def _create_gmail_service(self):
        """Authenticate and build the Gmail service."""
        creds = None
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception as e:
                logger.error(f"Error loading credentials from file: {e}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = Flow.from_client_secrets_file('client_secret.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Error in authentication flow: {e}")
                    raise

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service built successfully")
            return service
        except Exception as e:
            logger.error(f"Error building Gmail service: {e}")
            raise

    def get_recruiter_emails(self, user_id='me', query='', max_results=10):
        """Retrieve emails based on the given query."""
        service = self.get_service()

        try:
            results = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            logger.info(f"Retrieved {len(messages)} messages")
            return messages
        except HttpError as error:
            logger.error(f"An error occurred while retrieving emails: {error}")
            return []

    def get_email_content(self, message_id, user_id='me'):
        """Retrieve the content of a specific email."""
        service = self.get_service()

        try:
            message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
            payload = message['payload']
            headers = payload['headers']
            
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
            
            parts = payload.get('parts', [])
            body = ""
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            else:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

            logger.info(f"Retrieved content for email: {subject}")
            return {'subject': subject, 'sender': sender, 'body': body}
        except HttpError as error:
            logger.error(f"An error occurred while retrieving email content: {error}")
            return None

    def send_email(self, to, subject, body, user_id='me'):
        """Send an email using the Gmail API."""
        service = self.get_service()

        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent_message = service.users().messages().send(
                userId=user_id, body={'raw': raw_message}).execute()
            logger.info(f"Email sent successfully. Message ID: {sent_message['id']}")
            return sent_message
        except HttpError as error:
            logger.error(f"An error occurred while sending the email: {error}")
            return None

# Usage example
if __name__ == "__main__":
    gmail_service = GmailService()
    
    # Example: Get recruiter emails
    emails = gmail_service.get_recruiter_emails(query="from:recruiter@example.com")
    
    # Example: Get content of the first email
    if emails:
        email_content = gmail_service.get_email_content(emails[0]['id'])
        if email_content:
            print(f"Subject: {email_content['subject']}")
            print(f"From: {email_content['sender']}")
            print(f"Body: {email_content['body'][:100]}...")  # Print first 100 characters of the body
    
    # Example: Send an email
    # gmail_service.send_email("recipient@example.com", "Test Subject", "This is a test email.")