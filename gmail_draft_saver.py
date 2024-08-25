from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
import logging

def save_draft(service, original_message_id, response_body):
    try:
        message = MIMEText(response_body, 'html')
        original_message = service.users().messages().get(userId='me', id=original_message_id).execute()
        thread_id = original_message['threadId']
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(userId='me', body={
            'message': {
                'raw': raw,
                'threadId': thread_id
            }
        }).execute()
        return draft['id']
    except HttpError as error:
        logging.error(f'An error occurred while saving the draft: {error}')
        return None
