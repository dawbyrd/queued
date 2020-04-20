from datetime import datetime, date, time, timezone
import spotipy
import spotipy.util as util

def enum_tracks(tracks):
    for i, item in enumerate(tracks['items']):
        print(item['added_by']['id'].encode('utf-8'),item['added_at'].encode('utf-8'),item['track']['name'].encode('utf-8'))
        # print("   %d %32.32s %s" % (i, track['artists'][0]['name'].encode('utf-8'),
        #     track['name'].encode('utf-8')))

scope = 'playlist-read-private user-library-read user-read-private user-read-email user-read-currently-playing user-read-recently-played user-read-playback-state'
token = util.prompt_for_user_token('araaish',
                       scope,
                       client_id='8698031f9fa24db79f2074418f296b10',
                       client_secret='c2b602ae3ef1446f9d5164ca724ff318',
                       redirect_uri='http://localhost:8888/callback',
                       cache_path="tokens/.cache-araaish")


sp = spotipy.Spotify(auth=token)
usid = sp.current_user()['id']

results = sp.current_user_recently_played()
for i,item in enumerate(results['items']):
    track = item["track"]
    print(track['name'].encode('utf-8'))

playlists = sp.current_user_playlists()
ctracks = []
for playlist in playlists['items']:
    if playlist['owner']['id'] == usid:
        # print(playlist['owner']['id'])
        print(playlist['name'].encode('utf-8'))
        # print ('  total tracks', playlist['tracks']['total'])
        results = sp.playlist(playlist['id'],
            fields="tracks,next")
        tracks = results['tracks']
        enum_tracks(tracks)
        while tracks['next']: #this is because tracks can only hold 100 at a time? even within same playlist?
            tracks = sp.next(tracks)
            enum_tracks(tracks)
