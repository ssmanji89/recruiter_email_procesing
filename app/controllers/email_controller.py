from app.services.gmail_service import GmailService
from app.services.openai_service import OpenAIService

class EmailController:
    def __init__(self):
        self.gmail_service = GmailService()
        self.openai_service = OpenAIService()

    def process_emails(self):
        service = self.gmail_service.get_service()
        recruiter_emails = self.gmail_service.get_recruiter_emails(service)
        processed_emails = []

        for email in recruiter_emails:
            resume = self.openai_service.generate_tailored_resume(email.job_description, email.company_info)
            if resume:
                processed_emails.append((email, resume))

        return processed_emails
