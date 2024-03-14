"""
spotipy-analytics

- takes a backup of my Spotify library, including title/artist/year
- requires spotipy

"""

import os
import datetime
from statistics import mean
from typing import Dict, List
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from cabinet import Cabinet

cab = Cabinet()

# environment variables needed by Spotipy
os.environ['SPOTIPY_CLIENT_ID'] = cab.get("spotipy", "client_id")
os.environ['SPOTIPY_CLIENT_SECRET'] = cab.get(
    "spotipy", "client_secret")
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8888'
spotipy_username = cab.get("spotipy", "username")

csv_main_playlist = []
PATH_LOG = cab.get("path", "log")

def initialize_spotify_client() -> spotipy.Spotify:
    """Initializes and returns a Spotipy client instance."""
    try:
        client_credentials_manager = SpotifyClientCredentials()
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except Exception as e:
        cab.log(f"Could not initialize Spotify: {str(e)}", level="error")
        raise

def get_playlist_tracks(client: spotipy.Spotify, playlist_id: str) -> List[str]:
    """Retrieves tracks from a specified playlist."""
    playlist_tracks = []
    results = client.playlist_tracks(playlist_id)
    while results:
        for item in results['items']:
            if item['track']:
                track = item['track']
                track_info = (
                    f"{track['artists'][0]['name']}::"
                    f"{track['name']}::"
                    f"{track['album']['release_date']}::"
                    f"{track['external_urls']['spotify'] if not track['is_local'] else ''}"
                )
                playlist_tracks.append(track_info)
        results = client.next(results)  # Corrected indentation
    return playlist_tracks

def extract_playlists_tracks(client: spotipy.Spotify, playlists: List[str]) -> Dict[str, List[str]]:
    """Extracts tracks from all specified playlists."""
    tracks = {}
    for playlist in playlists:
        if ',' not in playlist:
            continue
        playlist_id, playlist_name = playlist.split(',', 1)
        cab.log(f"Getting tracks in {playlist_name}")
        tracks[playlist_name] = get_playlist_tracks(client, playlist_id)
    return tracks

def log_and_save(tracks: Dict[str, List[str]]):
    """Logs details and saves playlist tracks to a file."""

    all_tracks = [track for playlist in tracks.values() for track in playlist]
    # Updated to filter out 'None' or invalid date strings
    song_years = [
        int(track.split('::')[-2].split('-')[0])
        for track in all_tracks
        if track.split('::')[-2] and track.split('::')[-2] != 'None' and track.split('::')[-2].split('-')[0].isdigit()
    ]

    content = '\n'.join([f"{playlist}: {', '.join(tracks)}" for playlist, tracks in tracks.items()])
    file_name = f"{datetime.date.today()}.csv"
    file_path = f"{cab.get('path', 'cabinet', 'log-backup')}/log/songs/{file_name}"
    cab.write_file(content=content, file_name=file_name, file_path=file_path)

    cab.log("Updated Spotify Log")
    average_year = mean(song_years) if song_years else 0
    cab.put("spotipy", "average_year", str(average_year))
    cab.log(f"Setting average year to {average_year}")
    cab.log(f"{datetime.datetime.now().strftime('%Y-%m-%d')},{average_year}",
            log_name="SPOTIPY_AVERAGE_YEAR_LOG", log_folder_path=cab.get("path", "log"))

def extract():
    """Main function to extract and process Spotify playlists."""
    playlists = cab.get("spotipy", "playlists")
    if not playlists or len(playlists) < 2:
        cab.log("Could not resolve Spotify playlists", level="error")
        return

    client = initialize_spotify_client()
    tracks = extract_playlists_tracks(client, playlists)
    log_and_save(tracks)

    return tracks

def check_for_a_in_b(a_tracks, b_tracks, inverse=False, a_name='', b_name=''):
    """
    checks whether the item from Playlist A is in Playlist B
    logs an error or a success message depending on the results and "inverse"
    """

    is_not = ''
    if inverse:
        is_not = 'not '

    cab.log(
        f"Checking that every track in {a_name} is {is_not}in {b_name}",
        log_name="LOG_SPOTIFY")

    is_success = True
    for track in a_tracks:
        if (track in b_tracks) == inverse:
            is_success = False
            print(f"Is {track} in {b_name}? {track in b_tracks} {len(b_tracks)}")
            # cab.log(
            #     f"{track} {is_not}in {b_name}", log_name="LOG_SPOTIFY", level="error")
    if is_success:
        cab.log("Looks good!", log_name="LOG_SPOTIFY")


def check_for_one_match_in_playlists(tracks, playlist_name):
    """
    checks whether every track is in exactly one genre playlist (hardcoded)
    """

    msg = f"Checking that every track in {playlist_name} has exactly one genre playlist"
    cab.log(msg, log_name="LOG_SPOTIFY")

    tracks_in_genre_playlists = []
    for item in tracks[2:8]:
        tracks_in_genre_playlists += item[1]

    is_success = True
    for track in tracks[0][1]:
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
    cab.write_file(content=str(playlists_tracks),
        file_name="LOG_SPOTIPY_PLAYLIST_DATA", file_path=PATH_LOG)

    # Caution- this code is necessarily fragile and assumes the data in the `SPOTIPY_PLAYLISTS` file
    # matches the example file in README.md.

    tracks_list = list(playlists_tracks.values())
    tracks_names_list = list(playlists_tracks.keys())

    # 1. Check `Last 25 Added` and songs from each genre playlist are in `Tyler Radio`
    for i, playlist in enumerate(tracks_list[1:8]):
        check_for_a_in_b(tracks_list[i+1], tracks_list[0],
            False, tracks_names_list[i+1], tracks_names_list[0])

    # 2. Check that any song from `Removed` is not in `Tyler Radio`
    check_for_a_in_b(tracks_list[8], tracks_list[0],
        True, tracks_names_list[8], tracks_names_list[0])

    # 3. Check that songs from `Tyler Radio` have exactly one genre playlist
    # check_for_one_match_in_playlists(tracks_list, tracks_names_list)
