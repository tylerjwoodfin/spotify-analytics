"""
spotipy-analytics

- takes a backup of my Spotify library, including title/artist/year
- requires spotipy

"""

import os
import datetime
import sys
import pwd
from statistics import mean
import traceback
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from cabinet import Cabinet

cab = Cabinet()

userDir = pwd.getpwuid(os.getuid())[0]

# set environment variables needed by Spotipy
os.environ['SPOTIPY_CLIENT_ID'] = cab.get("spotipy", "client_id")
os.environ['SPOTIPY_CLIENT_SECRET'] = cab.get(
    "spotipy", "client_secret")
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8888'
spotipy_username = cab.get("spotipy", "username")

songYears = []
INDEX = 0
CSV_MAIN_PLAYLIST = ""
PATH_LOG = cab.get("path", "log")


def show_tracks_from_playlist(playlist_name, tracks, playlist_index, total_tracks):
    """
    iterates through a playlist and appends tracks to CSV_MAIN_PLAYLIST
    """

    global INDEX, CSV_MAIN_PLAYLIST
    return_tracks = []

    for i, item in enumerate(tracks['items']):
        track = item['track']
        INDEX += 1
        print(f"{INDEX} of {total_tracks} in {playlist_name}...")

        if track:
            if not track['is_local']:
                return_tracks.append(track['external_urls']['spotify'])
            if playlist_index == 0:
                CSV_MAIN_PLAYLIST += f"{str(INDEX)}::{track['artists'][0]['name']}::{track['name']}::{str(track['album']['release_date'])}::{(track['external_urls']['spotify'] if track['is_local'] == False else '')}\n"

                if track['album']['release_date']:
                    songYears.append(
                        int(track['album']['release_date'].split("-")[0]))

    return return_tracks


def get_playlist(client, playlist_id):
    """
    returns playlist given a spotipy client and playlist ID
    """

    return_playlist = ''

    try:
        return_playlist = client.playlist(playlist_id)
        return return_playlist
    except Exception as error:
        cab.log(
            f"Error parsing Spotify tracks: {str(error)}")
        return ''


def extract():
    """
    returns an array of tracks from all playlists
    writes playlist from CSV_MAIN_PLAYLIST to file
    """

    playlists = cab.get("spotipy", "playlists")

    try:
        client_credentials_manager = SpotifyClientCredentials()
        client = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager)
    except Exception as error:
        cab.log(
            f"Could not initialize Spotify: {str(error)}", level="error")

    if not playlists or len(playlists) < 2:
        cab.log("Could not resolve Spotify playlists", level="error")
        sys.exit()

    # array of playlist track arrays
    # e.g. playlists_tracks[0] is an array containing every track in playlists[0] ID
    return_playlists_tracks = []

    for index, item in enumerate(playlists):
        if not ',' in item:
            continue

        playlist_id = item.split(',')[0]
        playlist_name = item.split(',')[1]

        retries = 0
        results = ''
        while retries < 3 and results == '':
            cab.log(f"Getting Spotify playlist {playlist_id}")
            results = get_playlist(client, playlist_id)
            retries += 1
        if retries == 4:
            cab.log(
                f"Error parsing Spotify tracks after 3 retries: {str(error)}", level="error")
            sys.exit()

        tracks = results['tracks']
        total_tracks = results['tracks']['total']

        if index == 0:
            cab.put("spotipy", "total_tracks", total_tracks)

        playlist_tracks = []

        # go through each set of songs, 100 at a time (due to Spotipy limits)
        global INDEX
        INDEX = 0
        playlist_tracks += (show_tracks_from_playlist(playlist_name,
                            tracks, index, total_tracks))
        try:
            while tracks['next']:
                tracks = client.next(tracks)
                playlist_tracks += (show_tracks_from_playlist(playlist_name,
                                    tracks, index, total_tracks))
            return_playlists_tracks.append([playlist_name, playlist_tracks])
        except Exception:
            cab.log(
                f"Spotipy Error parsing {playlist_name}: {traceback.print_exc()}", level="error")

    cab.write_file(
        content=CSV_MAIN_PLAYLIST, file_name=f"{str(datetime.date.today())}.csv", file_path=f"{cab.get('path', 'cabinet', 'log-backup')}/log/songs/")
    cab.log("Updated Spotify Log")
    cab.put("spotipy", "average_year", mean(songYears))
    cab.log(datetime.datetime.now().strftime('%Y-%m-%d') + "," + str(mean(songYears)),
                   log_name="SPOTIPY_AVERAGE_YEAR_LOG", file_path=PATH_LOG)

    return return_playlists_tracks


def check_for_a_in_b(a_index, b_index, tracks, inverse=False):
    """
    checks whether the item from Playlist A is in Playlist B
    logs an error or a success message depending on the results and "inverse"
    """

    cab.log(
        f"Checking that every track in {tracks[a_index][0]} is {'not ' if inverse else ''}in {tracks[b_index][0]}", log_name="LOG_SPOTIFY")
    is_success = True
    for track in tracks[a_index][1]:
        if (not inverse and track not in tracks[b_index][1]) or (inverse and track in tracks[b_index][1]):
            is_success = False
            cab.log(
                f"{track} {'' if inverse else 'not '}in {tracks[b_index][0]}", log_name="LOG_SPOTIFY", level="error")
    if is_success:
        cab.log("Looks good!", log_name="LOG_SPOTIFY")


def check_for_one_match_in_playlists():
    """
    checks whether every track is in exactly one genre playlist (hardcoded)
    """

    msg = f"Checking that every track in {playlists_tracks[0][0]} has exactly one genre playlist"
    cab.log(msg, log_name="LOG_SPOTIFY")

    tracks_in_genre_playlists = []
    for item in playlists_tracks[2:8]:
        tracks_in_genre_playlists += item[1]

    is_success = True
    for track in playlists_tracks[0][1]:
        instance_count = tracks_in_genre_playlists.count(track)
        if instance_count == 0:
            cab.log(f"{track} missing a genre",
                           log_name="LOG_SPOTIFY", level="error")
            is_success = False
        elif instance_count > 1:
            cab.log(f"{track} found in multiple genres",
                           log_name="LOG_SPOTIFY", level="error")
            is_success = False

    if is_success:
        cab.log("Looks good!", log_name="LOG_SPOTIFY")


if __name__ == '__main__':
    playlists_tracks = extract()
    cab.write_file(content=str(
        playlists_tracks), file_name="LOG_SPOTIPY_PLAYLIST_DATA", file_path=PATH_LOG)

    # Caution- this code is necessarily fragile and assumes the data in the `SPOTIPY_PLAYLISTS` file
    # matches the example file in README.md.

    # 1. Check `Last 25 Added` and songs from each genre playlist are in `Tyler Radio`
    for i, playlist in enumerate(playlists_tracks[1:8]):
        check_for_a_in_b(i+1, 0, playlists_tracks)

    # 2. Check that any song from `Removed` is not in `Tyler Radio`
    check_for_a_in_b(8, 0, playlists_tracks, True)

    # 3. Check that songs from `Tyler Radio` have exactly one genre playlist
    check_for_one_match_in_playlists()
