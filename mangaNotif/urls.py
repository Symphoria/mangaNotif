from mangaNotif import app
from views import UserView, MangaView

app.add_url_rule('/users', view_func=UserView.as_view('user_view'))
app.add_url_rule('/manga', view_func=MangaView.as_view('manga_view'))
