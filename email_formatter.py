from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import os
import markdown2
import logging


def format_email_response(job_title, recruiter_name, resume):
    try:
        prompt = f"""
        Create a professional email response for a job application with the following details:
        Job Title: {job_title}
        Recruiter Name: {recruiter_name}
        Resume Summary: {resume[:200]}...

        The email should:
        1. Thank the recruiter for the opportunity
        2. Express enthusiasm for the position
        3. Briefly highlight 2-3 key qualifications from the resume
        4. Request a follow-up or interview
        5. Close professionally

        Format the response in Markdown.
        """

        response = client.completions.create(engine="text-davinci-002",
        prompt=prompt,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.7)

        markdown_content = response.choices[0].text.strip()
        html_content = markdown2.markdown(markdown_content)
        return html_content
    except Exception as e:
        logging.error(f"An error occurred while formatting the email response: {e}")
        return None
