from apscheduler.schedulers.blocking import BlockingScheduler
from mangaNotif.helper_functions import *

sched = BlockingScheduler()


@sched.scheduled_job('cron', day_of_week='mon-sun', hour=11, minute=42)
def scheduled_job():
    scrape_manga_data()


sched.start()
