# SpotifyPlaylistManagement
Checks for duplicate songs, unplayable songs, and songs missing from playlists.

## Dependencies
- [Secure Data](https://github.com/tylerjwoodfin/SecureData)
- [Spotipy](https://spotipy.readthedocs.io)

## Setup
1. Install Secure Data
2. Setup `Spotipy`
    - Place your Spotify client ID in your Secure Data data folder as `SPOTIPY_CLIENT_ID` (no extension)
    - Place your Spotify client secret in your Secure Data data folder as `SPOTIPY_CLIENT_SECRET` (no extension)
    - Place your Spotify username in your Secure Data data folder as `SPOTIPY_USERNAME` (no extension)
2. In your Secure Data data folder, create a file like the Example File below:
    - Name it `SPOTIPY_PLAYLISTS` (no extension). 
    - The first column is the `playlist ID`. The second column is just a label- make it anything you want. Mine are named after my playlists.
    - Replace my IDs with your Spotify playlist IDs.
    - Find your IDs by going to Spotify, right-clicking on a playlist, then clicking "Share".
    - e.g. https://open.spotify.com/playlist/**6hywO4jlkShcGKdTrez9yr**
3. Adjust the code as you see fit. Your musical tastes are your own. My code is specific to my own music setup, which is:
    - Each new song is added to `Tyler Radio`, `Last 25 Added`, and the appropriate `genre playlist`
    - No song should be in multiple `genre playlists`
    - No song should exist in `Tyler Radio` but not in a `genre playlist`
    - No song should exist in a `genre playlist` but not in `Tyler Radio`
    - No song should exist in `Last 25 Added` but not in `Tyler Radio`
    - No song should exist in `Removed` and `Tyler Radio` simultaneously.

## Usage
```python3 main.py```
(Note: this will take a minute. Spotipy limits you to 100 songs at a time.)

## Example File
```
6oqyTmCc2uf3aTDvZRk1T2,Tyler Radio
3ZDXHUzUcW6rLqOFpfK7QO,Last 25 Added
2OFLLecfoHrlwvJtfCJQoP,Hip Hop and Rap
3e691JWNU3anPtZgNfmFss,Party and EDM
2Aop8CO3DC7K9qyM1WgloX,Pop
4E8EyyhmbBUCAh9tNIYMv0,R&B
6hywO4jlkShcGKdTrez9yr,Rock
3zr0wmZocFR6nD6teH0dlm,Removed
```