from django.contrib.auth.backends import BaseBackend
from .models import MyUser

class EmployeeIDBackend(BaseBackend):
    # ユーザ認証実施
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            # MyUserモデルから入力したメールアドレスを持つユーザーを取得
            user = MyUser.objects.get(email=email)
        # テーブルデータが存在しない場合、例外発生
        except MyUser.DoesNotExist:
            return None
        # ユーザが存在する場合、パスワード一致チェック
        if user.check_password(password):
            return user
        # ユーザが存在しない場合、Noneを返却
        return None
    
    # メールアドレスからユーザーオブジェクトを取得 
    def get_user(self, email):
        try:
            return MyUser.objects.get(pk=email)
        except MyUser.DoesNotExist:
            return None
            