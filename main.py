from spotipy.oauth2 import SpotifyOAuth
from shazamio import Shazam, Serialize
from pathlib import Path
import spotipy
import asyncio
import string
import os

# Modify these variables
ClientID = "YOUR_CLIENT_ID"
ClientSecret = "YOUR_CLIENT_SECRET"
PlaylistName = "ToSpotify"
SongDir = "music"
SuccessDir = "done"
IgnoredDir = "ignored"

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

def moveFile(dir: string, file: string, ignored: bool = False) -> None:
    if ignored:
        os.rename(f"{dir}\{file}", f"{IgnoredDir}\{file}")
    else:
        os.rename(f"{dir}\{file}", f"{SuccessDir}\{file}")

async def getTrackID(songFile: string) -> string:
    print(f"Processing file: {songFile}")
    out = await sh.recognize_song(songFile)
    if len(out['matches']) != 0:
        serialized = Serialize.track(data=out["track"])
        print(f"Recognized song: {serialized.subtitle} - {serialized.title}")
        songSearch = sp.search(q=f'artist: "{serialized.subtitle}" track: "{serialized.title}"', limit=1)
        print(f"Song in Spotify: {songSearch['tracks']['items'][0]['artists'][0]['name']} - {songSearch['tracks']['items'][0]['name']}")
        return songSearch['tracks']['items'][0]['id']
    else:
        print("Couldn't recognize song. Skipping...")
        return "0"

if not os.path.isdir(SongDir):
    print(f"{SongDir} doesn't exist. Exiting...")
    exit(1)

if len(os.listdir(SongDir)) == 0:
    print(f"{SongDir} is empty. Exiting...")
    exit(1)

Path(IgnoredDir).mkdir(parents=False, exist_ok=True)
Path(SuccessDir).mkdir(parents=False, exist_ok=True)

playlistID = getPlaylistID(sp.current_user_playlists(limit=50))

for dir, subdir, files in os.walk(SongDir):
    for f in files:
        trackID = asyncio.run(getTrackID(f"{dir}\{f}"))
        if trackID != "0":
            songs.append(trackID)
            moveFile(dir, f)
        else:
            moveFile(dir, f, True)

print("Adding songs to playlist...")
sp.playlist_add_items(playlistID, songs)
print("Songs added!")
