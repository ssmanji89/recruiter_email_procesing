import os
import base64
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from dotenv import load_dotenv
import markdown2

# Load environment variables
load_dotenv()

# Set up OpenAI API key

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('gmail', 'v1', credentials=creds)

def get_recruiter_emails(service, user_id='me', max_results=10):
    try:
        # Search for recruiter emails
        query = "subject:(job OR opportunity OR position) newer_than:7d"
        results = service.users().messages().list(userId=user_id, q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No recruiter emails found.")
            return []

        recruiter_emails = []
        for message in messages:
            msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
            email_data = parse_email(msg)
            if email_data:
                recruiter_emails.append(email_data)

        return recruiter_emails

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def parse_email(msg):
    payload = msg['payload']
    headers = payload.get('headers', [])

    subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No Subject')
    sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown Sender')

    # Extract email body
    body = ""
    if 'parts' in payload:
        body = get_body_from_parts(payload['parts'])
    elif 'body' in payload:
        body = get_body_from_body(payload['body'])
    else:
        print(f"Unexpected email structure for subject: {subject}")

    # Extract job description and company information
    job_description = extract_job_description(body)
    company_info = extract_company_info(body)

    return {
        'subject': subject,
        'sender': sender,
        'body': body,
        'job_description': job_description,
        'company_info': company_info
    }

def get_body_from_parts(parts):
    for part in parts:
        if part['mimeType'] == 'text/plain':
            return decode_body(part['body'].get('data', ''))
        elif 'parts' in part:
            return get_body_from_parts(part['parts'])
    return ""

def get_body_from_body(body):
    return decode_body(body.get('data', ''))

def decode_body(data):
    if not data:
        return ""
    body_bytes = base64.urlsafe_b64decode(data)
    return body_bytes.decode('utf-8', errors='replace')

def extract_job_description(body):
    # Implement logic to extract job description from email body
    # This is a simplified example; you may need more sophisticated parsing
    match = re.search(r'Job Description:(.*?)(?=\n\n|\Z)', body, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_company_info(body):
    # Implement logic to extract company information from email body
    # This is a simplified example; you may need more sophisticated parsing
    match = re.search(r'Company:(.*?)(?=\n\n|\Z)', body, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

def generate_tailored_resume(job_description, company_info):
    prompt = f"""
    Given the following job description and company information, create a tailored resume in Markdown format:

    Job Description:
    {job_description}

    Company Information:
    {company_info}

    Generate a professional resume that highlights relevant skills and experiences for this specific job opportunity.
    Use Markdown formatting for structure and readability.
    """

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a professional resume writer."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=1000)

    return response.choices[0].message.content

import os
import base64
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from dotenv import load_dotenv
import markdown2
from PyPDF2 import PdfReader

# Load environment variables
load_dotenv()

# Set up OpenAI API key

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Path to your base PDF resume
BASE_RESUME_PATH = '/Users/sulemanmanji/Documents/GitHub/recruiter_email_processor/281.904.1969-Suleman S. Manji.pdf'

def get_base_resume_text():
    try:
        reader = PdfReader(BASE_RESUME_PATH)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading base resume PDF: {e}")
        return ""

base_resume_text = get_base_resume_text()

def generate_tailored_resume(job_description, company_info):
    prompt = f"""
    Given the following base resume, job description, and company information, create a tailored resume in Markdown format:

    Base Resume:
    {base_resume_text}

    Job Description:
    {job_description}

    Company Information:
    {company_info}

    Generate a professional resume that builds upon the base resume, highlighting and adjusting relevant skills and experiences for this specific job opportunity.
    Maintain the overall structure of the base resume but tailor the content to match the job requirements.
    Use Markdown formatting for structure and readability.
    """

    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500  # Increased token limit to accommodate base resume)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating resume: {e}")
        return "Unable to generate resume due to an error."

def main():
    service = get_gmail_service()
    recruiter_emails = get_recruiter_emails(service)

    for email in recruiter_emails:
        print(f"Processing email: {email['subject']}")
        tailored_resume = generate_tailored_resume(email['job_description'], email['company_info'])

        # Convert Markdown to HTML
        html_resume = markdown2.markdown(tailored_resume)

        # Here you would typically save or send the tailored resume
        # For demonstration, we'll just print it
        print("Tailored Resume (Markdown):")
        print(tailored_resume)
        print("\nTailored Resume (HTML):")
        print(html_resume)

if __name__ == '__main__':
    main()
