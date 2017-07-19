from mangaNotif import ma
from models import User, Manga


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        fields = ('username', 'email', 'send_mail_time')


class MangaSchema(ma.ModelSchema):
    class Meta:
        model = Manga
        fields = (
            'title', 'manga_url', 'author', 'artist', 'status', 'year_of_release', 'genres', 'info', 'cover_art_url',
            'latest_chapter', 'last_updated')
