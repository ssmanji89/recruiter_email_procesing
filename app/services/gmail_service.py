import os
import base64
import re
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models.email_model import Email

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    @staticmethod
    def get_service():
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logging.error(f"Failed to create Gmail service: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_recruiter_emails(service, user_id='me', max_results=10):
        try:
            query = "subject:(job OR opportunity) newer_than:7d"
            results = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])

            if not messages:
                logging.info("No recruiter emails found.")
                return []

            recruiter_emails = []
            for message in messages:
                try:
                    msg = service.users().messages().get(userId=user_id, id=message['id'], format='full').execute()
                    email_data = GmailService.parse_email(msg)
                    if email_data:
                        recruiter_emails.append(email_data)
                except Exception as e:
                    logging.error(f"Error processing email {message['id']}: {str(e)}", exc_info=True)

            logging.info(f"Retrieved {len(recruiter_emails)} recruiter emails.")
            return recruiter_emails

        except HttpError as error:
            logging.error(f"HTTP error occurred: {error}", exc_info=True)
            return []
        except Exception as e:
            logging.error(f"An unexpected error occurred while retrieving emails: {str(e)}", exc_info=True)
            return []

    @staticmethod
    def parse_email(msg):
        try:
            payload = msg['payload']
            headers = payload['headers']

            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), "No Subject")
            sender = next((header['value'] for header in headers if header['name'] == 'From'), "Unknown Sender")
            
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in payload:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

            job_description = GmailService.extract_job_description(body)
            company_info = GmailService.extract_company_info(body)

            return Email(subject, sender, body, job_description, company_info)
        except Exception as e:
            logging.error(f"Error parsing email: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def extract_job_description(body):
        match = re.search(r'Job Description:(.*?)(?=\n\n|\Z)', body, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def extract_company_info(body):
        match = re.search(r'Company:(.*?)(?=\n\n|\Z)', body, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
