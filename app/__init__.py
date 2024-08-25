from flask import Flask
from app.controllers.email_controller import EmailController
from app.views.email_view import EmailView

app = Flask(__name__)

@app.route('/')
def index():
    controller = EmailController()
    processed_emails = controller.process_emails()
    return EmailView.render_results(processed_emails)

if __name__ == '__main__':
    app.run(debug=True)
