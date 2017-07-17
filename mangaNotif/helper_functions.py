import subprocess
import json
import os
import sendgrid


def scrape_manga_data():
    subprocess.call("python manga_scraper.py", shell=True)
    with open('result.json', 'r+') as data_file:
        first_char = data_file.read(1)
        if first_char:
            data_file.seek(0)
            # data = data_file.read()
            manga_data = json.load(data_file)
            print manga_data
            # data_file.seek(0)
            # data_file.truncate()


def send_mail(receiver, email_template):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    data = {
        "personalizations": [
            {
                "to": [
                    {
                        "email": receiver
                    }
                ],
                "subject": "Confirm Account"
            }
        ],
        "from": {
            "email": "hj.harshit007@gmail.com"
        },
        "content": [
            {
                "type": "text/html",
                "value": email_template
            }
        ]
    }
    response = sg.client.mail.send.post(request_body=data)
