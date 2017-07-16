from mangaNotif import app
from views import UserView

app.add_url_rule('/users', view_func=UserView.as_view('user_view'))
