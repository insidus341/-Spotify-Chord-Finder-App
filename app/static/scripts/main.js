var previously_viewed_chords_url = null

function get_current_playing_song() {
    var playing_song_info = $.get( "/spotify/get_current_song", function(data) {

        if (data['ok'] == true)
        {
            process_playing_song_data(data['song'])
        }
        else {
            console.log("We were unable to get the chords URL, try again later")
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
    console.log(song['song_name'])
    console.log(song['chords_url'])
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

function get_song_html(chords_url) {
    var playing_song_html = $.get( "/spotify/get_song_page_html?url=" + chords_url, function(data) {
        console.log(data)
    })
}


    var playing_song_info = $.get( "/spotify/get_current_song", function(data) {

        if (data['ok'] == true)
        {
            process_playing_song_data(data['song'])
        }
        else {
            console.log("We were unable to get the chords URL, try again later")
        }
    })