import os
import logging
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.models.email_model import Email, ResponseEmail
from openai import OpenAI
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Update SCOPES to include send capability
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

class GmailService:
    def __init__(self):
        self.service = None
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_service(self):
        if not self.service:
            self.service = self._create_gmail_service()
        return self.service

    def _create_gmail_service(self):
        creds = None
        # Load credentials from token.json, refresh or re-authenticate if needed
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('gmail', 'v1', credentials=creds)
            return service
        except HttpError as error:
            logging.error(f'An error occurred: {error}')
            return None

    def get_recruiter_emails(self, user_id='me', max_results=11):
        try:
            service = self.get_service()

            # Contextual search query for recruiter-related emails
            query = 'subject:recruiter OR subject:job OR subject:hiring OR subject:opportunity'

            # Fetch list of messages in the inbox matching the query
            results = service.users().messages().list(
                userId=user_id, 
                labelIds=['INBOX'], 
                q=query, 
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            recruiter_emails = []

            for message in messages:
                # Fetch the full message content for each email
                msg = service.users().messages().get(
                    userId=user_id, 
                    id=message['id'], 
                    format='full'
                ).execute()

                # Filter the email for recruiter criteria
                if self.is_recruiter_email(msg):
                    email_data = self.parse_email(msg)
                    if email_data:
                        recruiter_emails.append(email_data)

            return recruiter_emails

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

    def is_recruiter_email(self, msg):
        """Filter method to determine if an email is from a recruiter."""
        headers = msg.get('payload', {}).get('headers', [])
        
        # Extract key headers like 'From' and 'Subject'
        from_header = next((header['value'] for header in headers if header['name'] == 'From'), None)
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), "").lower()

        # Define recruiter-related keywords or domains
        recruiter_keywords = ['recruiter', 'hiring', 'opportunity', 'position', 'job offer', 'talent acquisition']
        
        # Generate a prompt for OpenAI to analyze the email
        prompt = f"""
        The following email has the subject "{subject}" and body "{msg}" from {from_header}.
        Determine if this email is likely from a recruiter or contains job-related opportunities. 
        Respond with 'True' if it is, otherwise 'False'.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts job information from emails."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            return content.lower() == 'true'
        except Exception as e:
            logging.error(f"Error in is_recruiter_email: {e}")
            return False

    def parse_email(self, msg):
        headers = msg['payload']['headers']
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
        sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
        body = self.get_email_body(msg)
        
        extracted_data = self.extract_job_details(body)
        
        return Email(
            message_id=msg['id'],
            subject=subject,
            sender=sender,
            body=body,
            job_description=extracted_data.get('job_description', ''),
            company_info=extracted_data.get('company_info', ''),
            key_requirements=extracted_data.get('key_requirements', []),
            required_skills=extracted_data.get('required_skills', [])
        )

    def get_email_body(self, msg):
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(part['body']['data']).decode()
        elif 'body' in msg['payload']:
            return base64.urlsafe_b64decode(msg['payload']['body']['data']).decode()
        return ""
    
    def extract_job_details(self, email_body):
        # Ensure the email body is included in the prompt
        if not email_body.strip():
            logging.error("Email body is empty. Cannot proceed with extraction.")
            return {
                "job_description": "",
                "company_info": "",
                "key_requirements": [],
                "required_skills": []
            }

        # Prepare the prompt with the provided email body
        prompt = (
            "You are an assistant that helps parse recruiter emails. Extract the following information from the provided email body:\n\n"
            "Here is the format you should use for your response:\n\n"
            "{\n"
            "    \"job_description\": \"A concise summary of the job description.\",\n"
            "    \"company_info\": \"A concise summary of the company information.\",\n"
            "    \"key_requirements\": [\"Requirement 1\", \"Requirement 2\", \"Requirement 3\"],\n"
            "    \"required_skills\": [\"Skill 1\", \"Skill 2\", \"Skill 3\"]\n"
            "}\n\n"
            "Here is the email body:\n\n"
            f"{email_body}"
        )

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts job information from emails."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content.strip()
            logging.info(f"Received OpenAI response: {content}")

            # Check if the response is not JSON but a request for more input
            if "please provide" in content.lower():
                logging.error("OpenAI is asking for more input. Check the prompt and email body.")
                return {
                    "job_description": "",
                    "company_info": "",
                    "key_requirements": [],
                    "required_skills": []
                }

            # Clean the response to remove code block formatting, if present
            cleaned_content = self.clean_response_to_json(content)
            
            # Parse the cleaned content as JSON
            parsed_response = json.loads(cleaned_content)
            return parsed_response

        except json.JSONDecodeError as e:
            logging.error("Failed to parse OpenAI response as JSON")
            logging.error(f"OpenAI response: {content}")
            logging.error(f"JSONDecodeError: {e}")
            return {
                "job_description": "",
                "company_info": "",
                "key_requirements": [],
                "required_skills": []
            }
        except Exception as e:
            logging.error(f"Error in extract_job_details: {str(e)}")
            return {
                "job_description": "",
                "company_info": "",
                "key_requirements": [],
                "required_skills": []
            }

    def clean_response_to_json(self, response_text):
        """
        Cleans the OpenAI response to extract the JSON part by removing code block formatting.
        """
        try:
            # Remove code block markers (```json and ```)
            if response_text.startswith("```") and response_text.endswith("```"):
                # Extract the content inside the code block
                cleaned_text = response_text.strip("```").strip()
                
                # Check if it's wrapped with a language specifier (like ```json)
                if cleaned_text.startswith("json"):
                    cleaned_text = cleaned_text[len("json"):].strip()

                return cleaned_text

            # If no code block formatting is found, return the original response
            return response_text

        except Exception as e:
            logging.error(f"Error while cleaning the response: {e}")
            return "{}"  # Return empty JSON as a fallback




    def compose_response_email(self, original_email, user_profile, tailored_resume):
        prompt = f"""
        Compose a professional email response to a recruiter based on the following information:

        Original Email Subject: {original_email.subject}
        Job Description: {original_email.job_description}
        Company Info: {original_email.company_info}
        Applicant Name: {user_profile.name}
        Applicant Email: {user_profile.email}

        Key points to include:
        1. Express enthusiasm for the position
        2. Briefly mention 2-3 key skills that match the job requirements
        3. State that a tailored resume is attached
        4. Request an opportunity for an interview

        Keep the email concise (about 150-200 words), professional, and engaging.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional job applicant crafting a response to a recruiter."},
                    {"role": "user", "content": prompt}
                ]
            )
            response_body = response.choices[0].message.content.strip()
            subject = f"Re: {original_email.subject}"
            resume_pdf_path = os.path.join('app', 'generated_resumes', tailored_resume.pdf_filename)

            return ResponseEmail(original_email.sender, subject, response_body, resume_pdf_path)
        except Exception as e:
            logging.error(f"Error in compose_response_email: {e}")
            return None

    def send_email(self, response_email):
        try:
            service = self.get_service()
            message = MIMEMultipart()
            message['to'] = response_email.to
            message['subject'] = response_email.subject

            message.attach(MIMEText(response_email.body))

            with open(response_email.resume_pdf_path, 'rb') as file:
                attachment = MIMEApplication(file.read(), _subtype="pdf")
            attachment.add_header('Content-Disposition', 'attachment', filename='tailored_resume.pdf')
            message.attach(attachment)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            sent_message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            
            logging.info(f"Message sent. Message Id: {sent_message['id']}")
            response_email.sent = True
            return True
        except HttpError as error:
            logging.error(f'An error occurred: {error}')
            return False
