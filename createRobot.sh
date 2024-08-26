#!/bin/bash

# Comprehensive Update Script for Automated Recruiter Email Processing System

set -e

log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

handle_error() {
    log_message "ERROR: $1"
    exit 1
}

log_message "Starting comprehensive update for Automated Recruiter Email Processing System"

# Ensure we're in the project directory
PROJECT_DIR="recruiter_email_processor"
cd "$PROJECT_DIR" || handle_error "Failed to change to project directory"

# Activate virtual environment
source venv/bin/activate || handle_error "Failed to activate virtual environment"

# Update requirements
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client openai python-dotenv flask PyPDF2 xhtml2pdf markdown2
pip freeze > requirements.txt
log_message "Updated requirements"

# Update app/models/email_model.py
cat << 'EOF' > app/models/email_model.py
class Email:
    def __init__(self, message_id, subject, sender, body, job_description, company_info, key_requirements, required_skills):
        self.message_id = message_id
        self.subject = subject
        self.sender = sender
        self.body = body
        self.job_description = job_description
        self.company_info = company_info
        self.key_requirements = key_requirements
        self.required_skills = required_skills

class Resume:
    def __init__(self, content, html_content, matched_skills, pdf_filename):
        self.content = content
        self.html_content = html_content
        self.matched_skills = matched_skills
        self.pdf_filename = pdf_filename

class UserProfile:
    def __init__(self, name, email, resume_content):
        self.name = name
        self.email = email
        self.resume_content = resume_content

class ResponseEmail:
    def __init__(self, to, subject, body, resume_pdf_path):
        self.to = to
        self.subject = subject
        self.body = body
        self.resume_pdf_path = resume_pdf_path
        self.sent = False

class ProcessedEmail:
    def __init__(self, original_email, tailored_resume, response_email):
        self.original_email = original_email
        self.tailored_resume = tailored_resume
        self.response_email = response_email
EOF

log_message "Updated app/models/email_model.py"

# Update app/services/gmail_service.py
cat << 'EOF' > app/services/gmail_service.py
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
EOF

log_message "Updated app/services/gmail_service.py"

# Update app/services/openai_service.py
cat << 'EOF' > app/services/openai_service.py
import os
import logging
from openai import OpenAI
from app.models.email_model import Resume
import markdown2
from xhtml2pdf import pisa
import uuid

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OpenAIService:
    @staticmethod
    def generate_tailored_resume(email, user_profile):
        try:
            prompt = f"""
            Create a tailored resume based on the following:

            Job Description:
            {email.job_description}

            Company Information:
            {email.company_info}

            Key Requirements:
            {', '.join(email.key_requirements)}

            Required Skills:
            {', '.join(email.required_skills)}

            User's Existing Resume:
            {user_profile.resume_content}

            Generate a professional resume in Markdown format that highlights relevant skills and experiences.
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer."},
                    {"role": "user", "content": prompt}
                ]
            )

            resume_content = response.choices[0].message.content.strip()
            html_content = markdown2.markdown(resume_content)
            matched_skills = OpenAIService.match_skills(email.required_skills, resume_content)
            
            pdf_filename = OpenAIService.generate_pdf_resume(html_content, user_profile.name)
            
            return Resume(resume_content, html_content, matched_skills, pdf_filename)
        except Exception as e:
            logging.error(f"Error generating tailored resume: {str(e)}")
            return None

    @staticmethod
    def match_skills(required_skills, resume_content):
        return [skill for skill in required_skills if skill.lower() in resume_content.lower()]

    @staticmethod
    def generate_pdf_resume(html_content, user_name):
        try:
            unique_id = uuid.uuid4().hex[:8]
            filename = f"resume_{user_name.replace(' ', '_')}_{unique_id}.pdf"
            output_path = os.path.join('app', 'generated_resumes', filename)
            
            with open(output_path, "w+b") as result_file:
                pisa_status = pisa.CreatePDF(html_content, dest=result_file)
            
            if pisa_status.err:
                logging.error(f"Error generating PDF: {pisa_status.err}")
                return None
            
            return filename
        except Exception as e:
            logging.error(f"Error generating PDF resume: {str(e)}")
            return None
EOF

log_message "Updated app/services/openai_service.py"

# Update app/controllers/email_controller.py
cat << 'EOF' > app/controllers/email_controller.py
from app.services.gmail_service import GmailService
from app.services.openai_service import OpenAIService
from app.models.email_model import UserProfile, ProcessedEmail
from PyPDF2 import PdfReader

class EmailController:
    def __init__(self):
        self.gmail_service = GmailService()
        self.openai_service = OpenAIService()

    def process_emails(self, user_profile):
        recruiter_emails = self.gmail_service.get_recruiter_emails()
        processed_emails = []

        for email in recruiter_emails:
            tailored_resume = self.openai_service.generate_tailored_resume(email, user_profile)
            if tailored_resume:
                response_email = self.gmail_service.compose_response_email(email, user_profile, tailored_resume)
                processed_emails.append(ProcessedEmail(email, tailored_resume, response_email))

        return processed_emails

    def save_user_profile(self, name, email, resume_file):
        resume_content = self.extract_text_from_pdf(resume_file)
        return UserProfile(name, email, resume_content)

    def extract_text_from_pdf(self, pdf_file):
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    def send_approved_emails(self, approved_email_ids):
        for email_id in approved_email_ids:
            processed_email = next((pe for pe in self.processed_emails if pe.original_email.message_id == email_id), None)
            if processed_email:
                self.gmail_service.send_email(processed_email.response_email)
EOF

log_message "Updated app/controllers/email_controller.py"

# Update app/views/email_view.py
cat << 'EOF' > app/views/email_view.py
from flask import render_template, send_from_directory, jsonify
import os

class EmailView:
    @staticmethod
    def render_dashboard(processed_emails, user_profile):
        return render_template('dashboard.html', emails=processed_emails, user=user_profile)

    @staticmethod
    def render_profile_form():
        return render_template('profile_form.html')

    @staticmethod
    def download_resume(filename):
        return send_from_directory(os.path.join('app', 'generated_resumes'), filename, as_attachment=True)

    @staticmethod
    def render_email_sent(success):
        return jsonify({"success": success})
EOF

log_message "Updated app/views/email_view.py"

# Update app/__init__.py
cat << 'EOF' > app/__init__.py
from flask import Flask, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.controllers.email_controller import EmailController
from app.views.email_view import EmailView
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'app/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

controller = EmailController()
view = EmailView()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if 'resume_file' not in request.files:
            return "No file part"
        file = request.files['resume_file']
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            user_profile = controller.save_user_profile(name, email, file_path)
            processed_emails = controller.process_emails(user_profile)
            return view.render_dashboard(processed_emails, user_profile)
    return view.render_profile_form()

@app.route('/download/<filename>')
def download_resume(filename):
    return view.download_resume(filename)

@app.route('/send_emails', methods=['POST'])
def send_emails():
    approved_email_ids = request.json.get('approved_emails', [])
    success = controller.send_approved_emails(approved_email_ids)
    return view.render_email_sent(success)

if __name__ == '__main__':
    app.run(debug=True)
EOF

log_message "Updated app/__init__.py"

# Update app/templates/dashboard.html
cat << 'EOF' > app/templates/dashboard.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Processing Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <div class="container mt-5">
        <h1>Email Processing Dashboard for {{ user.name }}</h1>
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Select</th>
                    <th>Subject</th>
                    <th>Job Description</th>
                    <th>Resume</th>
                    <th>Response Preview</th>
                </tr>
            </thead>
            <tbody>
                {% for email in emails %}
                <tr>
                    <td><input type="checkbox" class="email-select" data-email-id="{{ email.original_email.message_id }}"></td>
                    <td>{{ email.original_email.subject }}</td>
                    <td>{{ email.original_email.job_description[:100] }}...</td>
                    <td><a href="{{ url_for('download_resume', filename=email.tailored_resume.pdf_filename) }}" class="btn btn-primary btn-sm">Download PDF</a></td>
                    <td>
                        <button class="btn btn-info btn-sm" data-bs-toggle="modal" data-bs-target="#responseModal{{ loop.index }}">Preview</button>
                        <div class="modal fade" id="responseModal{{ loop.index }}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-lg">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h5 class="modal-title">Response Email Preview</h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                    </div>
                                    <div class="modal-body">
                                        <p><strong>To:</strong> {{ email.response_email.to }}</p>
                                        <p><strong>Subject:</strong> {{ email.response_email.subject }}</p>
                                        <p><strong>Body:</strong></p>
                                        <pre>{{ email.response_email.body }}</pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <button id="sendSelectedEmails" class="btn btn-success">Send Selected Emails</button>
    </div>

    <script>
        $(document).ready(function() {
            $('#sendSelectedEmails').click(function() {
                var selectedEmails = [];
                $('.email-select:checked').each(function() {
                    selectedEmails.push($(this).data('email-id'));
                });

                if (selectedEmails.length > 0) {
                    $.ajax({
                        url: '/send_emails',
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify({approved_emails: selectedEmails}),
                        success: function(response) {
                            if (response.success) {
                                alert('Selected emails sent successfully!');
                                location.reload();
                            } else {
                                alert('Error sending emails. Please try again.');
                            }
                        },
                        error: function() {
                            alert('Error sending emails. Please try again.');
                        }
                    });
                } else {
                    alert('Please select at least one email to send.');
                }
            });
        });
    </script>
</body>
</html>
EOF

log_message "Updated app/templates/dashboard.html"

log_message "Comprehensive update script finished. The system now includes:"
log_message "1. Automated email processing workflow"
log_message "2. User dashboard for reviewing and approving responses"
log_message "3. Functionality to send approved emails"
log_message "Please ensure you have updated the SCOPES in your OAuth consent screen to include 'https://www.googleapis.com/auth/gmail.send'"
log_message "You may need to re-authenticate the application to grant the new permissions."
log_message "Update your .env file with the necessary API keys and credentials."
log_message "Run 'flask run' to start the updated application."

# Deactivate virtual environment
deactivate

log_message "Virtual environment deactivated. Setup and update script finished."
