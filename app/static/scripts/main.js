var previously_viewed_chords_url = null

function get_current_playing_song() {
    var playing_song_info = $.get( "/spotify/get_current_song", function(data) {

        if (data['ok'] == true)
        {
            song = data['song']
            process_playing_song_data(song)
        }
    })
        // .done(function() {
        // // console.log('second success')
        // })
        // .fail(function() {
        // // console.log('failed')
        // })
        // .always(function() {
        // // console.log('always')
        // });
}

$(function () {
    setInterval(get_current_playing_song, 2500);
});

$( document ).ready(function() {
    get_current_playing_song()
});


function process_playing_song_data(song) {
    console.log(song)
    chords_url = song['chords_url']

    if (chords_url != previously_viewed_chords_url)
    {
        set_iframe_url(chords_url)
        set_song_details_on_page(song)
    }
}

function set_iframe_url(url) {
    var main_iframe = $("#main_iframe")
    main_iframe.attr('src', url)
    main_iframe.show()

    previously_viewed_chords_url = chords_url
}

function set_song_details_on_page(song) {
    song_name = song['song_name']
    artist_name = song['artist_name']
    album_name = song['album_name']

    $('.song_name').html(song_name)
    $('.artist_name').html(artist_name)
}
