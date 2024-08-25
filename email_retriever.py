from googleapiclient.discovery import build
from oauth_setup import setup_oauth
import base64
import logging

def get_gmail_service():
    creds = setup_oauth()
    return build('gmail', 'v1', credentials=creds)

def list_recruiter_emails(service, user_id='me', max_results=10):
    try:
        query = "subject:(job OR opportunity)"
        results = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
        return results.get('messages', [])
    except Exception as error:
        logging.error(f'An error occurred while listing emails: {error}')
        return []

def get_email_content(service, user_id='me', msg_id=None):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        payload = message['payload']
        headers = payload['headers']
        
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')
        
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        else:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return {'id': msg_id, 'subject': subject, 'sender': sender, 'body': body}
    except Exception as error:
        logging.error(f'An error occurred while getting email content: {error}')
        return None
