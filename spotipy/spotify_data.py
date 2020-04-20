from gen_data import Artist, Song
import sys
import json
import os
import time
import spotipy
import spotipy.util as util
import numpy as np
from datetime import datetime, date, time, timezone
import dateutil.parser
import networkx as nx
from spotipy.oauth2 import SpotifyClientCredentials

def enum_tracks(tracks):
    out = []
    for i, item in enumerate(tracks['items']):
        out.append(item['track'])
        # print("   %d %32.32s %s" % (i, track['artists'][0]['name'].encode('utf-8'),
        #     track['name'].encode('utf-8')))
    return out

if __name__ == '__main__':

    scope = 'playlist-read-private user-library-read user-read-private user-read-email user-read-currently-playing user-read-recently-played user-read-playback-state'

    client_credentials_manager = SpotifyClientCredentials(client_id='8698031f9fa24db79f2074418f296b10', client_secret='c2b602ae3ef1446f9d5164ca724ff318')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    datastore = {"dict": {}, "decay": 10, "lradius": 5, "cvalue":1, "qvalue":1, "lastupdated": None}
    sg = Song(datastore["dict"], datastore["cvalue"], datastore["qvalue"], datastore["decay"])
    ctime = datetime.now(timezone.utc).isoformat()

    playlists = sp.user_playlists('spotify')
    ctracks = []
    while playlists:
        for i,playlist in enumerate(playlists['items']):
            print(playlist['name'].encode('utf-8'))
            print ('total tracks', playlist['tracks']['total'])
            results = sp.playlist(playlist['id'],
                fields="tracks,next")
            tracks = results['tracks']
            ctracks.extend(enum_tracks(tracks))

            while tracks['next']: #this is because tracks can only hold 100 at a time? even within same playlist?
                tracks = sp.next(tracks)
                ctracks.extend(enum_tracks(tracks))

            sz = len(ctracks)
            print(sz)
            for i in range(sz):
                for j in range(sz):
                    if(ctracks[i] == None or ctracks[j] == None): continue
                    if(ctracks[i]['id'] == None or ctracks[j]['id'] == None): continue
                    sg.add_edge(ctracks[i], ctracks[j],ctime,sz,100)
            ctracks.clear()

        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None

        datastore["dict"] = sg.export_dict()
        datastore["lastupdated"] = ctime
        datastore["valid"] = True

        with open("data/json/spotify2.json", 'w') as fp:
            json.dump(datastore, fp)
            print("saved succesfully")
