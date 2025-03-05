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
