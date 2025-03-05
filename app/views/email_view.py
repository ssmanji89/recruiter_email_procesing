from flask import render_template, send_from_directory, jsonify
import os

class EmailView:
    @staticmethod
    def render_dashboard(processed_emails, user_profile):
        return render_template('dashboard.html', emails=processed_emails, user=user_profile)

    @staticmethod
    def render_profile_form():
        return render_template('profile_form.html')

    @staticmethod
    def download_resume(filename):
        return send_from_directory(os.path.join('app', 'generated_resumes'), filename, as_attachment=True)

    @staticmethod
    def render_email_sent(success):
        return jsonify({"success": success})
