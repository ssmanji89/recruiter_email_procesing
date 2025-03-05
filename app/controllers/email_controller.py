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
