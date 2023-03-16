# SpotifyPlaylistManagement
Checks for duplicate songs, unplayable songs, and songs missing from playlists.

## Dependencies
- [Spotify API access](https://stevesie.com/docs/pages/spotify-client-id-secret-developer-api)
- [Cabinet](https://github.com/tylerjwoodfin/cabinet)
- [Spotipy](https://spotipy.readthedocs.io)

## Setup
1. Obtain [Spotify API access](https://stevesie.com/docs/pages/spotify-client-id-secret-developer-api). Make note of the client ID and secret.
2. Install [Cabinet](https://github.com/tylerjwoodfin/cabinet)
3. Setup `Spotipy`
    - In cabinet's `settings.json`, add your Spotify data using `Example settings.json` below as a template.
    - Find your `playlist IDs` by going to Spotify, right-clicking on a playlist, then clicking "Share".
        - The ID is the last part of the URL, for instance: https://open.spotify.com/playlist/6hywO4jlkShcGKdTrez9yr
    - The first column in `playlists` is the `playlist ID`. The second column is just a label- make it anything you want. Mine are named after my playlists.
4. Adjust the code as you see fit. Your musical tastes are your own. My code is specific to my own music setup, which is:
    - Each new song is added to `Tyler Radio`, `Last 25 Added`, and the appropriate `genre playlist`
    - No song should be in multiple `genre playlists`
    - No song should exist in `Tyler Radio` but not in a `genre playlist`
    - No song should exist in a `genre playlist` but not in `Tyler Radio`
    - No song should exist in `Last 25 Added` but not in `Tyler Radio`
    - No song should exist in `Removed` and `Tyler Radio` simultaneously.

## Usage
```python3 main.py```
(Note: this will take a minute. Spotipy limits you to 100 songs at a time.)

## Example settings.json
```
"spotipy": {
    "playlists": [
        "6oqyTmCc2uf3aTDvZRk1T2,Tyler Radio",
        "3ZDXHUzUcW6rLqOFpfK7QO,Last 25 Added",
        "09jNP5fuQesZoC7xiIj5I4,Chill",
        "2OFLLecfoHrlwvJtfCJQoP,Hip Hop and Rap",
        "3e691JWNU3anPtZgNfmFss,Party and EDM",
        "2Aop8CO3DC7K9qyM1WgloX,Pop",
        "4E8EyyhmbBUCAh9tNIYMv0,R&B",
        "6hywO4jlkShcGKdTrez9yr,Rock",
        "3zr0wmZocFR6nD6teH0dlm,Removed"
    ],
    "client_secret": "your_secret_here",
    "client_id": "your_id_here",
    "username": "your_spotify_username"
}
```
