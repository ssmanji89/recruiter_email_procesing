from flask import Flask, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.controllers.email_controller import EmailController
from app.views.email_view import EmailView
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'app/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

controller = EmailController()
view = EmailView()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if 'resume_file' not in request.files:
            return "No file part"
        file = request.files['resume_file']
        if file.filename == '':
            return "No selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            user_profile = controller.save_user_profile(name, email, file_path)
            processed_emails = controller.process_emails(user_profile)
            return view.render_dashboard(processed_emails, user_profile)
    return view.render_profile_form()

@app.route('/download/<filename>')
def download_resume(filename):
    return view.download_resume(filename)

@app.route('/send_emails', methods=['POST'])
def send_emails():
    approved_email_ids = request.json.get('approved_emails', [])
    success = controller.send_approved_emails(approved_email_ids)
    return view.render_email_sent(success)

if __name__ == '__main__':
    app.run(debug=True)
