from app.core.controllers.settings import get_env
from app.core.singleton import Singleton

import sys
import mariadb

@Singleton
class Database(object):
    db_connection_attempts = 0

    def __init__(self):
        try:
            self._setup()
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            self.database_connection = None
            sys.exit(1)
        

    # Initlize our database connection
    # If we throw an error here we'll exit the application
    def _setup(self):
        
        conn = mariadb.connect(
            user=get_env('DATABASE_USER'),
            password=get_env('DATABASE_SECRET'),
            host=get_env('DATABASE_IP'),
            port=int(get_env('DATABASE_PORT')),
            database=get_env('DATABASE_SELECTED')
        )

        conn.auto_reconnect = True

        self.database_connection = conn

    def _get_cursor(self):
        try:
            if self.database_connection is None:
                self._setup()
                self.database_connection.ping()
            else:
                self.database_connection.ping()

        except:
            if self.db_connection_attempts == 0:
                self.db_connection_attempts = 1
                self.database_connection = None
                
                try:
                    cursor = self._get_cursor()
                    self.db_connection_attempts = 0
                    return cursor

                except:
                    raise Exception('Failed database connection retry')

            else:
                self.db_connection_attempts = 0
                raise Exception('Database connection failed')

        return self.database_connection.cursor()

    def _insert(self, statement, values):
        cursor = self._get_cursor()
        cursor.execute(statement, values)
        self.database_connection.commit()
        cursor.close()

        return cursor.lastrowid


    def _update(self, statement, values):
        cursor = self._get_cursor()
        cursor.execute(statement, values)
        self.database_connection.commit()
        cursor.close()

    def _read(self, statement, values):
        cursor = self._get_cursor()
        cursor.execute(statement, values)
        record = cursor.fetchall()
        cursor.close()

        if len(record) == 0:
            return None
        else:
            return record[0][1]

    def _delete(self, statement, values):
        cursor = self._get_cursor()
        cursor.execute(statement, values)
        self.database_connection.commit()
        rowcount = cursor.rowcount
        cursor.close()

        return rowcount


    # Inserts an authentication challenge into the database
    # These are used later in read_spotify_authorization_challenge()
    def insert_spotify_authorization_challenge(self, random_state, clients_ip_addr):
        if random_state is None or not isinstance(random_state, str):
            raise ValueError()
        if clients_ip_addr is None or not isinstance(clients_ip_addr, str):
            raise ValueError()

        try:
            sql = "INSERT INTO authentication_challenges (challenge, clients_ip_addr) VALUES (%s, %s)"
            values = (random_state, clients_ip_addr)
            self._insert(sql, values)

            # attempt to return the random state that we added
            # this confirms that the state was saved
            return random_state

        except:
            raise Exception("Unable to insert authentication challenge into the database")

    # Read authentication challenges from the database
    # Matching against the state and the clients public IP address
    def read_spotify_authorization_challenge(self, spotify_state, connected_clients_ip):
        if connected_clients_ip is None or not isinstance(connected_clients_ip, str):
            raise ValueError()
        if spotify_state is None or not isinstance(spotify_state, str):
            raise ValueError()

        try:
            sql = "SELECT id, challenge, generated FROM authentication_challenges WHERE clients_ip_addr = ? AND challenge = ? ORDER BY id DESC LIMIT 1;"
            values = (connected_clients_ip, spotify_state)

            return self._read(sql, values)

        except:
            raise Exception("Database connection failed")

    def delete_spotify_authorization_challenge(self, state):
        try:
            sql = "DELETE FROM authentication_challenges WHERE challenge = ?"
            values = (state,)
            return self._delete(sql, values)

        except:
            raise Exception("Database connection failed")

    # Checks the `users` table for the Spotify user
    # Returns the user ID if the Spotify ID exists
    def read_spotify_user_id_from_spotify_id(self, spotify_user_id):
        print("checking for exisiting user: {0}".format(spotify_user_id))
        try:
            sql = "SELECT id FROM users WHERE spotify_user_id = ?"
            values = (spotify_user_id,)

            record = self._read(sql, values)

            if record is None:
                return None

            # If we did find a result, return the users id
            user_id = record[0][0]
            return user_id

        except:
            raise Exception("read_spotify_user_id_from_spotify_id: Unable to read the user from the database")

    # Get spotify user data
    def read_spotify_user_data(self, user_id):
        try:
            sql = "SELECT id, spotify_user_id, name, email, url, last_login_time, last_login_ip, country_code FROM users WHERE id = ?"
            values = (user_id,)

            record = self._read(sql, values)

            # If we didn't find a user return None
            if record is None:
                return None

            # If we found the user, return it
            return record

        except:
            raise Exception("read_spotify_user_data: Unable to read the user from the database")

    # Insert a new Spotify user
    def insert_spotify_user(self, spotify_user_data, connected_clients_ip):
        if spotify_user_data is None or not isinstance(spotify_user_data, dict):
            raise ValueError()

        try:
            user_id = spotify_user_data['id']
            user_email = spotify_user_data['email']
            user_display_name = spotify_user_data['display_name']
            user_url = spotify_user_data['href']
            user_country = spotify_user_data['country']

            sql = "INSERT INTO users (spotify_user_id, name, email, url, last_login_ip, country_code) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (user_id, user_display_name, user_email, user_url, connected_clients_ip, user_country)

            row_id = self._insert(sql, values)

            # return the row id
            return row_id

        except:
            raise Exception("Unable to save the user in the Database")

    # Insert the users Access and Refresh tokens
    # Can only be called once we have a user id
    def insert_spotify_user_access_tokens(self, user_id, token_data):
        if token_data is None or not isinstance(token_data, dict):
            raise ValueError()

        try:
            access_token = token_data['access_token']
            refresh_token = token_data['refresh_token']
            token_expires = token_data['expires_in']
            token_scope = token_data['scope']

            sql = "INSERT INTO authentications (user_id, access_token, refresh_token, expires_in, scope) VALUES (%s, %s, %s, %s, %s)"
            values = (user_id, access_token, refresh_token, token_expires, token_scope)

            row_id = self._insert(sql, values)

            # Return the row ID that was created
            return row_id

        except:
            raise Exception("Database connection failed")

    def read_user_access_tokens(self, user_id):
        if user_id is None or not isinstance(user_id, int):
            raise ValueError()

        try:
            sql = "SELECT * FROM authentications WHERE user_id = ? ORDER BY id desc LIMIT 1"
            values = (user_id,)

            record = self._read(sql, values)
            return record

        except:
            raise Exception("Database connection failed")

    def update_user_access_token(self, user_id, new_access_tokens, includes_refresh_token = False):
        if new_access_tokens is None or not isinstance(new_access_tokens, dict):
            raise ValueError()

        if includes_refresh_token:
            access_token = new_access_tokens['access_token']
            refresh_token = new_access_tokens['refresh_token']
            expires_in = new_access_tokens['expires_in']
            scope = new_access_tokens['scope']

            sql = "UPDATE authentications SET access_token = ?, refresh_token = ?, expires_in = ?, scope = ? WHERE user_id = ?"
            values = (access_token, refresh_token, expires_in, scope, user_id)

        else:
            access_token = new_access_tokens['access_token']
            expires_in = new_access_tokens['expires_in']
            scope = new_access_tokens['scope']

            sql = "UPDATE authentications SET access_token = ?, expires_in = ?, scope = ? WHERE user_id = ?"
            values = (access_token, expires_in, scope, user_id)
        
        try:
            self._update(sql, values)

        except:
            raise Exception("Database connection failed")

    def insert_user_login_token(self, user_id, login_token, expires_in):
        try:
            sql = "INSERT INTO user_login_tokens (user_id, login_token, expires_in) VALUES (?, ?, ?)"
            values = (user_id, login_token, expires_in)

            row_id = self._insert(sql, values)

            # Return the token ID that was created
            return row_id

        except:
            raise Exception("Database connection failed")

    def read_user_login_token(self, token_id, user_id):
        try:
            sql = "SELECT login_token, generated, expires_in FROM user_login_tokens WHERE id = ? AND user_id = ?"
            values = (token_id, user_id)

            record = self._read(sql, values)

            # Return the user record
            return record

        except:
            raise Exception("Database connection failed")

    def update_user_login_token(self, token_id, user_id):
        try:
            sql = "UPDATE user_login_tokens SET generated = CURRENT_TIMESTAMP() WHERE id = ? AND user_id = ?"
            values = (token_id, user_id)  

            self._update(sql, values)  

        except:
            raise Exception("Database connection failed")

    def delete_user_login_token(self, token_id, user_id):
        try:
            sql = "DELETE FROM user_login_tokens WHERE id = ? AND user_id = ?"
            values = (token_id, user_id)

            self._delete(sql, values)

        except:
            raise Exception("Database connection failed")

    def read_song_data(self, spotify_uri):
        try:
            sql = "SELECT id, name, artist, album, spotify_uri, chords_url, date_added FROM songs WHERE spotify_uri = ?"
            values = (spotify_uri,)
            record = self._read(sql, values)

            # Return the user record
            return record

        except:
            raise Exception("Database connection failed")

    def insert_song_data(self, name, artist, album, spotify_uri, chords_url):
        try:
            sql = "INSERT INTO songs (name, artist, album, spotify_uri, chords_url) VALUES (?, ?, ?, ?, ?)"
            values = (name, artist, album, spotify_uri, chords_url)
           
            row_id = self._insert(sql, values)

            # Return the token ID that was created
            return row_id

        except:
            raise Exception("Database connection failed")
