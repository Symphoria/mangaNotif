import json
import os
import sendgrid
from mangaNotif import db
from models import Manga, UserManga
import datetime


def scrape_manga_data():
    os.system("python mangaNotif/manga_scraper.py")
    with open('mangaNotif/result.json', 'r+') as data_file:
        first_char = data_file.read(1)

        if first_char:
            data_file.seek(0)
            manga_data_list = json.load(data_file)
            data_file.seek(0)
            data_file.truncate()

            for manga_data in manga_data_list:
                manga = Manga.query.filter_by(title=manga_data['name']).first()

                if manga:
                    manga.latest_chapter = manga_data['chapter_name'].split()[-1]
                    manga.last_updated = datetime.datetime.now()

                    user_manga_list = UserManga.query.filter_by(manga_id=manga.id, in_track_list=True)
                    for user_manga_obj in user_manga_list:
                        user_manga_obj.send_mail = True

            db.session.commit()


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
