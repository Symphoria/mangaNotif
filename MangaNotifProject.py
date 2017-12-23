from mangaNotif import app, scheduler

scheduler.start()
app.run(port=8000, debug=True, use_reloader=False)
