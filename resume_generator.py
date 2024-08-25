from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import os
import logging


def generate_resume(job_description, user_profile):
    try:
        prompt = f"""
        Given the following job description and user profile, generate a tailored resume:

        Job Description:
        {job_description}

        User Profile:
        {user_profile}

        Generate a professional resume that highlights the user's relevant skills and experiences for this job.
        """

        response = client.completions.create(engine="text-davinci-002",
        prompt=prompt,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.7)

        return response.choices[0].text.strip()
    except Exception as e:
        logging.error(f"An error occurred while generating the resume: {e}")
        return None
