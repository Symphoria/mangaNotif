import json
import os
import sendgrid
from sqlalchemy import extract
from serializers import MangaSchema
from models import *
import datetime
from email_templates import send_notif_template


def send_mail(receiver, email_template, subject):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    data = {
        "personalizations": [
            {
                "to": [
                    {
                        "email": receiver
                    }
                ],
                "subject": subject
            }
        ],
        "from": {
            "email": "hj.harshit007@gmail.com",
            "name": "Hoodwink"
        },
        "content": [
            {
                "type": "text/html",
                "value": email_template
            }
        ]
    }
    response = sg.client.mail.send.post(request_body=data)


def send_notif_mail():
    users = User.query.filter(extract('hour', User.send_mail_time) == datetime.datetime.now().hour,
                              User.is_active == True).all()

    for user in users:
        user_manga_obj_list = UserManga.query.filter_by(user_id=user.id, send_mail=True)
        manga_id_list = [obj.manga_id for obj in user_manga_obj_list]
        track_listed_manga = Manga.query.filter(Manga.id.in_(manga_id_list))
        manga_schema = MangaSchema(many=True)
        result = manga_schema.dump(track_listed_manga)

        for manga in result.data:
            if len(manga['title']) > 14:
                manga['title'] = manga['title'][:13] + "..."

        template = send_notif_template(result.data)
        send_mail(user.email, template, "Today's Updates")

        for user_manga in user_manga_obj_list:
            user_manga.send_mail = False

        db.session.commit()


def scrape_manga_data():
    os.system("python mangaNotif/manga_scraper.py")
    with open('mangaNotif/result.json', 'r+') as data_file:
        first_char = data_file.read(1)

        if first_char:
            data_file.seek(0)
            manga_data_list = json.load(data_file)

            for manga_data in manga_data_list:
                manga = Manga.query.filter_by(title=manga_data['name']).first()

                if manga:
                    manga.latest_chapter = manga_data['chapter_name'].split()[-1]
                    manga.last_updated = datetime.datetime.now()

                    user_manga_list = UserManga.query.filter_by(manga_id=manga.id, in_track_list=True)
                    for user_manga_obj in user_manga_list:
                        user_manga_obj.send_mail = True

            db.session.commit()
            data_file.seek(0)
            data_file.truncate()
            send_notif_mail()
