from csv import excel_tab
from shutil import move
from tokenize import Ignore
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from spotipy.oauth2 import SpotifyOAuth
from shazamio import Shazam
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
UnknownDir = f"{IgnoredDir}/unknown"
NotFoundDir = f"{IgnoredDir}/not_found"
AlwaysUseAlternativeSearch = False  # Always use artist + name instead of isrc
mkt = "IT"  # Select your Spotify market (or leave it blank)

# But not these ones
scope = "playlist-read-private, playlist-modify-private"
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=scope,
        client_id=ClientID,
        client_secret=ClientSecret,
        redirect_uri="http://localhost:8888/callback",
    )
)
sh = Shazam()
songs = []

progressbar = Progress(
    SpinnerColumn(),
    *Progress.get_default_columns(),
    TimeElapsedColumn(),
)


def getPlaylistID(playlists: list) -> string:
    for item in playlists["items"]:
        if item["name"] == PlaylistName:
            progressbar.console.log(f"Found playlist {PlaylistName}")
            return item["id"]

    userID = sp.me()["id"]
    playlist = sp.user_playlist_create(
        userID, PlaylistName, public=False, collaborative=False
    )
    progressbar.console.log(f"Created playlist {PlaylistName}")
    return playlist["id"]


def moveFile(
    dir: string, file: string, ignored: bool = False, recognized: bool = False, exception: bool = False
) -> None:
    if ignored:
        if exception:
            os.rename(f"{dir}{file}", f"{IgnoredDir}/{file}")
        else:
            if recognized:
                os.rename(f"{dir}{file}", f"{NotFoundDir}/{file}")
            else:
                os.rename(f"{dir}{file}", f"{UnknownDir}/{file}")
    else:
        os.rename(f"{dir}/{file}", f"{SuccessDir}/{file}")


async def getTrackID(songFile: string) -> string:
    progressbar.console.log(f"Processing file: {songFile}")
    out = await sh.recognize_song(songFile)
    if len(out["matches"]) != 0:
        progressbar.console.log(
            f"Recognized song: {out['track']['subtitle']} - {out['track']['title']}"
        )
        
        if "isrc" in out["track"]:
            songSearch = sp.search(
                q=f'isrc: "{out["track"]["isrc"]}"', type="track", market=mkt, limit=1
            )

        try:
            sSearchItems = len(songSearch["tracks"]["items"])
        except UnboundLocalError:
            sSearchItems = 0

        if (
            AlwaysUseAlternativeSearch
            or sSearchItems == 0
            or "isrc" not in out["track"]
        ):
            progressbar.console.log("Using alternative search")
            songSearch = sp.search(
                q=f'artist: "{out["track"]["subtitle"]}" track: "{out["track"]["title"]}"',
                type="track",
                market=mkt,
                limit=1,
            )

        if len(songSearch["tracks"]["items"]) != 0:
            progressbar.console.log(
                f"Song in Spotify: {songSearch['tracks']['items'][0]['artists'][0]['name']} - {songSearch['tracks']['items'][0]['name']}"
            )
            return songSearch["tracks"]["items"][0]["id"]
        else:
            progressbar.console.log(
                "Song was recognized, but wasn't found in Spotify. Skipping..."
            )
            return "1"
    else:
        progressbar.console.log("Shazam couldn't recognize song. Skipping...")
        return "0"


if not os.path.isdir(SongDir):
    progressbar.console.log(f"{SongDir} doesn't exist. Exiting...")
    exit(1)

if len(os.listdir(SongDir)) == 0:
    progressbar.console.log(f"{SongDir} is empty. Exiting...")
    exit(1)

# Path(IgnoredDir).mkdir(parents=False, exist_ok=True)
Path(UnknownDir).mkdir(parents=True, exist_ok=True)
Path(NotFoundDir).mkdir(parents=False, exist_ok=True)
Path(SuccessDir).mkdir(parents=False, exist_ok=True)

playlistID = getPlaylistID(sp.current_user_playlists(limit=50))

paths = [f"{dir}/{f}" for dir, subdir, files in os.walk(SongDir) for f in files]

with progressbar as prog:
    process = prog.add_task("[green]Processing...", total=len(paths), start=True)
    for f in paths:
        try:
            trackID = asyncio.run(getTrackID(f))
            if trackID == "0":
                moveFile(
                    f.replace("\\", "/")[: f.rfind("/")],
                    f.replace("\\", "/")[f.rfind("/") :],
                    True,
                )
            elif trackID == "1":
                moveFile(
                    f.replace("\\", "/")[: f.rfind("/")],
                    f.replace("\\", "/")[f.rfind("/") :],
                    True,
                    True,
                )
            else:
                songs.append(trackID)
                moveFile(
                    f.replace("\\", "/")[: f.rfind("/")],
                    f.replace("\\", "/")[f.rfind("/") :],
                )
        except Exception as e:
            progressbar.console.log(f"Exception occurred, file will be put into {IgnoredDir}\nException follows:\n{e}")
            moveFile(
                    f.replace("\\", "/")[: f.rfind("/")],
                    f.replace("\\", "/")[f.rfind("/") :],
                    True,
                    False,
                    True,
                )
        prog.update(process, advance=1)
        if len(songs) == 50:
            progressbar.console.log("Adding songs to playlist...")
            sp.playlist_add_items(playlistID, songs)
            songs.clear()

progressbar.console.log("Adding songs to playlist...")
sp.playlist_add_items(playlistID, songs)
progressbar.console.log("Songs added!")
