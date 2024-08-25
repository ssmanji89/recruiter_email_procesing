class Email:
    def __init__(self, subject, sender, body, job_description, company_info):
        self.subject = subject
        self.sender = sender
        self.body = body
        self.job_description = job_description
        self.company_info = company_info

class Resume:
    def __init__(self, content, html_content):
        self.content = content
        self.html_content = html_content
