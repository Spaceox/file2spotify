# file2spotify
 Convert your music files to Spotify tracks

# Usage

1. Download and install [Python](https://www.python.org/downloads/)
2. Install the dependences in requirements.txt with pip (`pip install -r requirements.txt`)
3. Download [ffmpeg](https://www.ffmpeg.org/download.html) and extract it in the script directory
4. Create a Spotify app like this:
	- Login with your Spotify account [here](https://developer.spotify.com/dashboard/)
	- Click "Create an app", and fill out the form
	- Click "Edit settings", select "Redirect URIs" and put this in `http://localhost:8888/callback`
	- Click Add, then Save
5. Copy the Client ID and Client Secret into the Python file, replacing `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET`
	- Now you can also change the playlist name (`PlaylistName`) and the name of the directory containing your songs (`SongDir`)
6.  Dump your music into a folder called music (or whatever you set `SongDir` in the python file) in the script's directory
7. Run `main.py`