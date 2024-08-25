import os
import logging
from openai import OpenAI
from app.models.email_model import Resume
import markdown2

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OpenAIService:
    @staticmethod
    def generate_tailored_resume(job_description, company_info):
        try:
            prompt = f"""
            Given the following job description and company information, create a tailored resume in Markdown format:

            Job Description:
            {job_description}

            Company Information:
            {company_info}

            Generate a professional resume that highlights relevant skills and experiences for this specific job opportunity.
            Use Markdown formatting for structure and readability.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )

            resume_content = response.choices[0].message.content.strip()
            html_content = markdown2.markdown(resume_content)
            return Resume(resume_content, html_content)
        except Exception as e:
            logging.error(f"Error generating tailored resume: {str(e)}", exc_info=True)
            return None
