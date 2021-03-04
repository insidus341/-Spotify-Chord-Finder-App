# from app import app

from flask import Flask, request, redirect, render_template

from app.core.main_handler import Core
from app.core.controllers.settings import get_env

import requests
import json
import os

# ********************************************* #
app = Flask(__name__)
app.config['SECRET_KEY'] = get_env('APP_SECRET')
app.config['PERMANENT_SESSION_LIFETIME'] = int(get_env('USER_LOGIN_TOKEN_LIFETIME'))
# ********************************************* #

core = Core.Instance()

@app.route('/')
def home():

    try:
        returning_user = core.returning_user()
    except:
        return render_template('error.html')

    if returning_user:
        user_details = core.get_user_details()
        username = user_details[2]

        return render_template('index_authed.html', username=username)
    else:
        return render_template('index.html', returning_user=returning_user)

@app.route('/login', methods=["GET"])
def login():
    connected_clients_ip = request.remote_addr
    connected_clients_user_agent = request.user_agent

    try:
        redirect_url = core.user_login(connected_clients_ip)
    except:
        return render_template('error.html')

    if redirect_url is False or redirect_url is None or "https://accounts.spotify.com" not in redirect_url:
        return "Login failed"
    
    return redirect(redirect_url, 302)

@app.route('/logout', methods=["GET"])
def logout():
    try:
        core.user_logout()
    except:
        return render_template('error.html')

    return redirect(get_env('APP_URL'), 302)

@app.route('/spotify/callback', methods=["GET"])
def spotify_callback():
    connected_clients_ip = request.remote_addr
    connected_clients_user_agent = request.user_agent

    if 'code' in request.args and 'state' in request.args:
        spotify_code = request.args.get('code')
        spotify_state = request.args.get('state')

        try:
            core.spotify_callback(connected_clients_ip, spotify_code, spotify_state)
        except:
            return render_template('error.html')

    return redirect(get_env('APP_URL'), 302)

@app.route('/spotify/get_current_song', methods=["GET"])
def spotify_get_current_song():
    connected_clients_ip = request.remote_addr
    
    try:
        current_song = core.get_current_playing_song()
    except:
        return render_template('error.html')

    output = {
        "ok": False
    }

    if current_song:
        output = current_song
        
    return output

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=8000
    )