from flask import render_template

class EmailView:
    @staticmethod
    def render_results(processed_emails):
        return render_template('results.html', emails=processed_emails)
