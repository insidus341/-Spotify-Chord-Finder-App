from app.core.controllers.database import Database
from app.core.controllers.settings import get_env
from app.core.singleton import Singleton
from flask import session as Flask_Session

import secrets

@Singleton
class Session():

    def __init__(self):
        self.database = Database.Instance()

    def create_user_login_token(self, user_id):
        print("creating session data") 
        
        secure_token = self.generate_secure_user_login_token()
        token_expiration_time = get_env('USER_LOGIN_TOKEN_LIFETIME') # 30 days

        token_row_id = self.database.insert_user_login_token(user_id, secure_token, token_expiration_time)
        if token_row_id is not None:
            self.save_user_login_token_to_browser(user_id, token_row_id, secure_token)

    def generate_secure_user_login_token(self):
        secure_token = secrets.token_hex()
        return secure_token

    def save_user_login_token_to_browser(self, user_id, token_id, session_token):
        Flask_Session['user_id'] = user_id
        Flask_Session['token_id'] = token_id
        Flask_Session['session_token'] = session_token 
        Flask_Session.permanent = True 
    
    def check_if_user_session_exists(self):
        if 'token_id' in Flask_Session and 'user_id' in Flask_Session and 'session_token' in Flask_Session:
            return True
        else:
            return False

    def check_if_user_session_token_is_valid(self):
        if self.check_if_user_session_exists():
            token_id = Flask_Session['token_id']
            user_id = Flask_Session['user_id']
            session_token = Flask_Session['session_token']

            stored_session_token = self.database.read_user_login_token(token_id, user_id)
            if stored_session_token is not None and stored_session_token[0][0] == session_token:
                return True

        return False

    def update_user_session_token(self):
        if self.check_if_user_session_exists():
            token_id = Flask_Session['token_id']
            user_id = Flask_Session['user_id']
            self.database.update_user_login_token(token_id, user_id)

    def delete_user_session_token(self):
        # users session is valid, let's delete it from our database
        if self.check_if_user_session_token_is_valid():
            token_id = Flask_Session['token_id']
            user_id = Flask_Session['user_id']
            session_token = Flask_Session['session_token']

            self.database.delete_user_login_token(token_id, user_id)
        
        self.delete_user_session_token_from_browser()

    def delete_user_session_token_from_browser(self):
        if self.check_if_user_session_exists():
            Flask_Session.pop('token_id', None)
            Flask_Session.pop('user_id', None)
            Flask_Session.pop('session_token', None)

    def get_user_id_from_session(self):
        if not self.check_if_user_session_token_is_valid():
            return False
        
        return Flask_Session['user_id']