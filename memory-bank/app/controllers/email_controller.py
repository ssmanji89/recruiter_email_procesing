import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from app.services.gmail_service import GmailService
from app.services.openai_service import OpenAIService
from app.models.email_model import UserProfile

class EmailController:
    def __init__(self):
        self.gmail_service = GmailService()
        self.openai_service = OpenAIService()

    def process_emails(self, user_profile):
        service = self.gmail_service.get_service()
        recruiter_emails = self.gmail_service.get_recruiter_emails(service)
        processed_emails = []

        for email in recruiter_emails:
            resume = self.openai_service.generate_tailored_resume(email, user_profile)
            if resume:
                processed_emails.append((email, resume))

        return processed_emails

    def save_user_profile(self, name, email, resume_file):
        filename = secure_filename(resume_file.filename)
        file_path = os.path.join('app', 'uploads', filename)
        resume_file.save(file_path)
        
        resume_content = self.extract_text_from_pdf(file_path)
        
        return UserProfile(name, email, resume_content)

    def extract_text_from_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
