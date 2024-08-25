from flask import render_template, request, send_from_directory
import os

class EmailView:
    @staticmethod
    def render_results(processed_emails, user_profile):
        return render_template('results.html', emails=processed_emails, user=user_profile)

    @staticmethod
    def render_profile_form():
        return render_template('profile_form.html')

    @staticmethod
    def download_resume(filename):
        return send_from_directory(os.path.join('app', 'generated_resumes'), filename, as_attachment=True)
