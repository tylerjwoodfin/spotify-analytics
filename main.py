# ReadMe
# Takes a backup of my Spotify music library, including title, artist, and year, and places the csv in a log folder in my Dropbox directory.
# Uses "Spotipy", a great tool to use the Spotify APIs.
# Mail was installed using msmtp. sudo apt-get install msmtp msmtp-mta
# Config file: /etc/msmtprc

from spotipy.oauth2 import SpotifyClientCredentials
import os
from os import path
import datetime
import sys
import subprocess
import spotipy
import pwd
import codecs
from statistics import mean

userDir = pwd.getpwuid( os.getuid() )[ 0 ]

sys.path.insert(0, f'/home/{userDir}/Git/SecureData')
import secureData


# set environment variables needed by Spotipy
os.environ['SPOTIPY_CLIENT_ID'] = secureData.variable("SPOTIPY_CLIENT_ID")
os.environ['SPOTIPY_CLIENT_SECRET'] = secureData.variable("SPOTIPY_CLIENT_SECRET")
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8888'
spotipy_username = secureData.variable("SPOTIPY_USERNAME")

songYears = []
index = 0

def show_tracks(tracks, playlistName, total_tracks):
    global index
    returnTracks = []

    for i, item in enumerate(tracks['items']):
        track = item['track']
        index+=1
        print(f"{index} of {total_tracks} in {playlistName}...")

        if track['is_local'] == False:
            returnTracks.append(track['external_urls']['spotify'])
    
    return returnTracks

def extract():
    playlists = secureData.array("SPOTIPY_PLAYLISTS")

    try:
        client_credentials_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except Exception as e:
        secureData.log(f"Caught Spotify Initialization Error: {str(e)}")

    if(not playlists):
        sys.exit()

    # array of playlist track arrays, e.g. playlists_tracks[0] is an array containing every track in playlists[0] ID
    playlists_tracks = []
    
    for playlist in playlists:
        if(not ',' in playlist):
            continue

        playlist_id = playlist.split(',')[0]
        playlist_name = playlist.split(',')[1]
        results = sp.playlist(playlist_id)
        tracks = results['tracks']
        total_tracks = results['tracks']['total']

        playlist_tracks = []

        # go through each set of songs, 100 at a time (due to API limits)
        global index
        index = 0
        playlist_tracks += (show_tracks(tracks, playlist_name, total_tracks))
        while tracks['next']:
            tracks = sp.next(tracks)
            playlist_tracks += (show_tracks(tracks, playlist_name, total_tracks))
        
        playlists_tracks.append([playlist_name, playlist_tracks])
            
    return playlists_tracks

def checkForAinB(a_index, b_index, tracks):
    secureData.log(f"Checking that every track in {tracks[a_index][0]} is in {tracks[b_index][0]}", logName="LOG_SPOTIFY")
    success = True
    for track in tracks[a_index][1]:
        if(track not in tracks[b_index][1]):
            success = False
            secureData.log(f"{track} not in {tracks[b_index][0]}", logName="LOG_SPOTIFY")
    if(success):
        secureData.log(f"Looks good!", logName="LOG_SPOTIFY")

if __name__ == '__main__':
    playlists_tracks = extract()
    secureData.write("SPOTIPY_PLAYLIST_DATA", str(playlists_tracks))

    # Caution- this code is necessarily fragile and assumes the data in the `SPOTIPY_PLAYLISTS` file
    # matches the example file in README.md.

    # 1. Check `Last 25 Added` and songs from each genre playlist is in `Tyler Radio`
    for i, playlist in enumerate(playlists_tracks[1:]):
        checkForAinB(i+1, 0, playlists_tracks)