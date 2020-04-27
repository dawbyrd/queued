import json_to_nx
import spotipy
import spotipy.util as util
import networkx as nx
import sys

# TODO: make this process faster by only adding edges and nodes that don't already exist

client_id = '8698031f9fa24db79f2074418f296b10'
client_secret='c2b602ae3ef1446f9d5164ca724ff318'
redirect_uri='http://localhost:8888/callback'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        scope = 'playlist-read-private user-library-read user-read-private user-read-email user-read-currently-playing user-read-recently-played user-read-playback-state'
        users = sys.argv[1:]
        for u in users:
            t = util.prompt_for_user_token(u, scope,client_id=client_id, client_secret=client_secret,redirect_uri=redirect_uri,cache_path="tokens/.cache-"+u)
            if t:
                sp = spotipy.Spotify(auth=t)
                usid = sp.current_user()['id']
                sG, aG, gG = json_to_nx.main([usid+".json", 'song', 'artist', 'genre'])
                nx.write_gexf(sG, "data/gexf/S"+usid+".gexf")
                nx.write_gexf(aG, "data/gexf/A"+usid+".gexf")
                nx.write_gexf(gG, "data/gexf/G"+usid+".gexf")
            else:
                print("Can't get tokens for "+u)
    else:
        print("Usage: %s usernames" % (sys.argv[0],))
