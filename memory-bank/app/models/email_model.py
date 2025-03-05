class Email:
    def __init__(self, subject, sender, body, job_description, company_info, key_requirements, required_skills):
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
