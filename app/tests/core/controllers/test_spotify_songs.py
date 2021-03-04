import sys

def test_spotify_songs_init():
    from app.core.controllers.spotify_songs import Spotify_songs
    spotify_songs = Spotify_songs.Instance()

    assert spotify_songs is not None

def test_get_chords_url_from_google_search_api():
    from app.core.controllers.spotify_songs import Spotify_songs
    spotify_songs = Spotify_songs.Instance()

    url = spotify_songs.google_search("plug in baby", "muse")
    print(url)
    assert type(url) == str
