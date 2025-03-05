import os
import logging
from openai import OpenAI
from app.models.email_model import Resume
import markdown2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from xhtml2pdf import pisa
import uuid

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OpenAIService:
    @staticmethod
    def generate_tailored_resume(email, user_profile):
        try:
            prompt = f"""
            You are a professional resume writer tasked with creating a tailored resume for a specific job opportunity. Use the information provided below to create a resume that highlights the candidate's relevant skills and experiences.

            JOB INFORMATION:
            Job Title: {email.subject}
            Company: {email.company_info}
            Job Description: {email.job_description}
            Key Requirements:
            {', '.join(email.key_requirements)}
            Required Skills:
            {', '.join(email.required_skills)}

            CANDIDATE INFORMATION:
            Name: {user_profile.name}
            Email: {user_profile.email}
            Existing Resume:
            {user_profile.resume_content}

            INSTRUCTIONS:
            Create a professional resume using the following template. Fill in the sections with relevant information from the candidate's existing resume, tailored to match the job requirements. Use Markdown for formatting and structure the data as shown in the JSON-like format below:

            ```
            {
                "resume": {
                    "header": {
                        "name": "Candidate's Full Name",
                        "email": "candidate@email.com",
                        "phone": "Phone Number",
                        "location": "City, State"
                    },
                    "summary": "A brief, impactful professional summary highlighting key skills and experiences relevant to the job.",
                    "skills": [
                        "Skill 1 relevant to the job",
                        "Skill 2 relevant to the job",
                        "..."
                    ],
                    "experience": [
                        {
                            "title": "Most Recent Job Title",
                            "company": "Company Name",
                            "date": "Start Date - End Date",
                            "responsibilities": [
                                "Key responsibility or achievement",
                                "Another key responsibility or achievement",
                                "..."
                            ]
                        },
                        {
                            "title": "Previous Job Title",
                            "company": "Company Name",
                            "date": "Start Date - End Date",
                            "responsibilities": [
                                "Key responsibility or achievement",
                                "Another key responsibility or achievement",
                                "..."
                            ]
                        }
                    ],
                    "education": [
                        {
                            "degree": "Degree Name",
                            "institution": "Institution Name",
                            "date": "Graduation Year"
                        }
                    ],
                    "certifications": [
                        "Relevant Certification 1",
                        "Relevant Certification 2",
                        "..."
                    ]
                }
            }
            ```

            Use this structure to create a Markdown-formatted resume. Ensure that:
            1. The content is tailored to address the specific job requirements and skills.
            2. Experiences and skills most relevant to the job opportunity are highlighted.
            3. Achievements and responsibilities are quantifiable where possible.
            4. The resume is concise and well-structured, limited to 1-2 pages worth of content.

            Please generate the tailored resume now:
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer specializing in tailoring resumes to specific job opportunities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500
            )

            resume_content = response.choices[0].message.content.strip()
            html_content = markdown2.markdown(resume_content)
            matched_skills = OpenAIService.match_skills(email.required_skills, resume_content)
            
            pdf_filename = OpenAIService.generate_pdf_resume(html_content, user_profile.name, email.subject)
            
            return Resume(resume_content, html_content, matched_skills, pdf_filename)
        except Exception as e:
            logging.error(f"Error generating tailored resume: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def match_skills(required_skills, resume_content):
        matched = [skill for skill in required_skills if skill.lower() in resume_content.lower()]
        return matched

    @staticmethod
    def generate_pdf_resume(html_content, user_name, job_subject):
        try:
            unique_id = uuid.uuid4().hex[:8]
            filename = f"resume_{user_name.replace(' ', '_')}_{unique_id}.pdf"
            output_path = os.path.join('app', 'generated_resumes', filename)
            
            # Convert HTML to PDF
            with open(output_path, "w+b") as result_file:
                pisa_status = pisa.CreatePDF(html_content, dest=result_file)
            
            if pisa_status.err:
                logging.error(f"Error generating PDF: {pisa_status.err}")
                return None
            
            return filename
        except Exception as e:
            logging.error(f"Error generating PDF resume: {str(e)}", exc_info=True)
            return None
