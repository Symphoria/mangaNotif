from apscheduler.schedulers.blocking import BlockingScheduler
from mangaNotif.helper_functions import *

sched = BlockingScheduler()


@sched.scheduled_job('cron', day_of_week='mon-sun', hour=23, minute=56)
def scheduled_job():
    scrape_manga_data()


sched.start()
