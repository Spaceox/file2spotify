import string
from shazamio import Shazam, Serialize
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import asyncio
import os

# Modify these variables
ClientID = "YOUR_CLIENT_ID"
ClientSecret = "YOUR_CLIENT_SECRET"
PlaylistName = "ToSpotify"
SongDir = "music"

# But not these ones
scope = 'playlist-read-private, playlist-modify-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=ClientID, client_secret=ClientSecret, redirect_uri="http://localhost:8888/callback"))
sh = Shazam()
songs = []

def getPlaylistID(playlists: list) -> string:
    for item in playlists['items']:
        if item['name'] == PlaylistName:
            print(f"Found playlist {PlaylistName}")
            return item['id']

    userID = sp.me()['id']
    playlist = sp.user_playlist_create(userID, PlaylistName, public=False, collaborative=False)
    print(f"Created playlist {PlaylistName}")
    return playlist['id']

async def getTrackID(songFile: string) -> string:
    print(f"Processing file: {songFile}")
    out = await sh.recognize_song(songFile)
    serialized = Serialize.track(data=out["track"])
    print(f"Recognized song: {serialized.subtitle} - {serialized.title}")
    songSearch = sp.search(q=f'artist: "{serialized.subtitle}" track: "{serialized.title}"', limit=1)
    print(f"Song in Spotify: {songSearch['tracks']['items'][0]['artists'][0]['name']} - {songSearch['tracks']['items'][0]['name']}")
    return songSearch['tracks']['items'][0]['id']

if not os.path.isdir(SongDir):
    print(f"{SongDir} doesn't exist. Exiting...")
    exit(1)

if len(os.listdir(SongDir)) == 0:
    print(f"{SongDir} is empty. Exiting...")
    exit(1)

playlistID = getPlaylistID(sp.current_user_playlists(limit=50))

for dir, subdir, files in os.walk(SongDir):
    for f in files:
        trackID = asyncio.run(getTrackID(f"{dir}\{f}"))
        songs.append(trackID)

print("Adding songs to playlist...")
sp.playlist_add_items(playlistID, songs)
print("Songs added!")
