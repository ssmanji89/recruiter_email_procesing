import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QMessageBox
from email_retriever import get_gmail_service, list_recruiter_emails, get_email_content
from resume_generator import generate_resume
from email_formatter import format_email_response
from gmail_draft_saver import save_draft

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recruiter Email Processor")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        
        self.process_button = QPushButton("Process Emails")
        self.process_button.clicked.connect(self.process_emails)
        layout.addWidget(self.process_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def process_emails(self):
        try:
            service = get_gmail_service()
            messages = list_recruiter_emails(service)
            
            for message in messages:
                email_content = get_email_content(service, msg_id=message['id'])
                if email_content:
                    resume = generate_resume(email_content['body'], "Your user profile here")
                    response = format_email_response(email_content['subject'], email_content['sender'], resume)
                    draft_id = save_draft(service, email_content['id'], response)
                    
                    log_message = f"Processed email: {email_content['subject']}\nDraft saved with ID: {draft_id}\n"
                    self.log_output.append(log_message)
                    logging.info(log_message)

            QMessageBox.information(self, "Success", "All emails processed successfully!")
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.log_output.append(error_message)
            logging.error(error_message)
            QMessageBox.critical(self, "Error", error_message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
