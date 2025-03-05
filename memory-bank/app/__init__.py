from flask import Flask, request, redirect, url_for
from app.controllers.email_controller import EmailController
from app.views.email_view import EmailView

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'app/uploads'
app.config['GENERATED_RESUMES_FOLDER'] = 'app/generated_resumes'
controller = EmailController()
view = EmailView()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        resume_file = request.files['resume']
        user_profile = controller.save_user_profile(name, email, resume_file)
        processed_emails = controller.process_emails(user_profile)
        return view.render_results(processed_emails, user_profile)
    return view.render_profile_form()

@app.route('/download/<filename>')
def download_resume(filename):
    return view.download_resume(filename)

if __name__ == '__main__':
    app.run(debug=True)
