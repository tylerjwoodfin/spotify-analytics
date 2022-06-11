# ReadMe
# Takes a backup of my Spotify music library, including title, artist, and year, and places the csv in a log folder in my Dropbox directory.
# Uses "Spotipy", a great tool to use the Spotify APIs.
# Mail was installed using msmtp. sudo apt-get install msmtp msmtp-mta
# Config file: /etc/msmtprc

from spotipy.oauth2 import SpotifyClientCredentials
import os
import datetime
import sys
import spotipy
import pwd
from statistics import mean
from securedata import securedata

userDir = pwd.getpwuid(os.getuid())[0]

# set environment variables needed by Spotipy
os.environ['SPOTIPY_CLIENT_ID'] = securedata.getItem("spotipy", "client_id")
os.environ['SPOTIPY_CLIENT_SECRET'] = securedata.getItem(
    "spotipy", "client_secret")
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8888'
spotipy_username = securedata.getItem("spotipy", "username")

songYears = []
index = 0
mainPlaylistCSV = ""
PATH_LOG = securedata.getItem("path", "log")


def show_tracks(playlist_name, tracks, playlist_index, total_tracks):
    global index, mainPlaylistCSV, songYears
    returnTracks = []

    for i, item in enumerate(tracks['items']):
        track = item['track']
        index += 1
        print(f"{index} of {total_tracks} in {playlist_name}...")

        if track:
            if not track['is_local']:
                returnTracks.append(track['external_urls']['spotify'])
            if playlist_index == 0:
                mainPlaylistCSV += f"{str(index)}::{track['artists'][0]['name']}::{track['name']}::{str(track['album']['release_date'])}::{(track['external_urls']['spotify'] if track['is_local'] == False else '')}\n"

                if(track['album']['release_date']):
                    songYears.append(
                        int(track['album']['release_date'].split("-")[0]))

    return returnTracks


def extract():
    playlists = securedata.getItem("spotipy", "playlists")

    try:
        client_credentials_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager)
    except Exception as e:
        securedata.log(
            f"Could not initialize Spotify: {str(e)}", level="error")

    if(not playlists or len(playlists) < 2):
        securedata.log(f"Could not resolve Spotify playlists", level="error")
        sys.exit()

    # array of playlist track arrays, e.g. playlists_tracks[0] is an array containing every track in playlists[0] ID
    playlists_tracks = []

    try:
        for i, playlist in enumerate(playlists):
            if(not ',' in playlist):
                continue

            playlist_id = playlist.split(',')[0]
            playlist_name = playlist.split(',')[1]
            results = sp.playlist(playlist_id)
            tracks = results['tracks']
            total_tracks = results['tracks']['total']

            if(i == 0):
                securedata.setItem("spotipy", "total_tracks", total_tracks)

            playlist_tracks = []

            # go through each set of songs, 100 at a time (due to Spotipy limits)
            global index
            index = 0
            playlist_tracks += (show_tracks(playlist_name,
                                tracks, i, total_tracks))
            while tracks['next']:
                tracks = sp.next(tracks)
                playlist_tracks += (show_tracks(playlist_name,
                                    tracks, i, total_tracks))

            playlists_tracks.append([playlist_name, playlist_tracks])

        securedata.writeFile(
            content=mainPlaylistCSV, fileName=f"{str(datetime.date.today())}.csv", filePath=f"{securedata.getItem('path', 'securedata', 'log-backup')}/log/songs/")
        securedata.log("Updated Spotify Log")
        securedata.setItem("spotipy", "average_year", mean(songYears))
        securedata.log(datetime.datetime.now().strftime('%Y-%m-%d') + "," + str(mean(songYears)),
                       logName="SPOTIPY_AVERAGE_YEAR_LOG", filePath=PATH_LOG)

        return playlists_tracks
    except Exception as e:
        securedata.log(
            f"Error parsing Spotify tracks: {str(e)}", level="error")
        sys.exit()


def checkForAInB(a_index, b_index, tracks, inverse=False):

    securedata.log(
        f"Checking that every track in {tracks[a_index][0]} is {'not ' if inverse else ''}in {tracks[b_index][0]}", logName="LOG_SPOTIFY")
    isSuccess = True
    for track in tracks[a_index][1]:
        if((not inverse and track not in tracks[b_index][1]) or (inverse and track in tracks[b_index][1])):
            isSuccess = False
            securedata.log(
                f"{track} {'' if inverse else 'not '}in {tracks[b_index][0]}", logName="LOG_SPOTIFY", level="error")
    if(isSuccess):
        securedata.log("Looks good!", logName="LOG_SPOTIFY")


def checkForOneMatchInGenrePlaylists():
    securedata.log(
        f"Checking that every track in {playlists_tracks[0][0]} has exactly one genre playlist", logName="LOG_SPOTIFY")
    tracks_in_genre_playlists = []
    for item in playlists_tracks[2:7]:
        tracks_in_genre_playlists += item[1]

    isSuccess = True
    for track in playlists_tracks[0][1]:
        instance_count = tracks_in_genre_playlists.count(track)
        if instance_count == 0:
            securedata.log(f"{track} missing a genre",
                           logName="LOG_SPOTIFY", level="error")
            isSuccess = False
        elif instance_count > 1:
            securedata.log(f"{track} found in multiple genres",
                           logName="LOG_SPOTIFY", level="error")
            isSuccess = False

    if isSuccess:
        securedata.log("Looks good!", logName="LOG_SPOTIFY")


if __name__ == '__main__':
    playlists_tracks = extract()
    securedata.writeFile(content=str(
        playlists_tracks), fileName="LOG_SPOTIPY_PLAYLIST_DATA", filePath=PATH_LOG)

    # Caution- this code is necessarily fragile and assumes the data in the `SPOTIPY_PLAYLISTS` file
    # matches the example file in README.md.

    # 1. Check `Last 25 Added` and songs from each genre playlist are in `Tyler Radio`
    for i, playlist in enumerate(playlists_tracks[1:7]):
        checkForAInB(i+1, 0, playlists_tracks)

    # 2. Check that any song from `Removed` is not in `Tyler Radio`
    checkForAInB(7, 0, playlists_tracks, True)

    # 3. Check that songs from `Tyler Radio` have exactly one genre playlist
    checkForOneMatchInGenrePlaylists()
