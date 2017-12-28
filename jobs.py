from apscheduler.schedulers.blocking import BlockingScheduler
from mangaNotif.helper_functions import *

sched = BlockingScheduler()


@sched.scheduled_job('cron', day_of_week='mon-sun', hour=14, minute=15)
def scheduled_job():
    scrape_manga_data()


sched.start()
