from mangaNotif import ma
from models import User


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        fields = ('username', 'email', 'send_mail_time')
