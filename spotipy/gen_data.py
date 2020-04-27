import json
import os
import time
import sys
import spotipy
import spotipy.util as util
import numpy as np
from datetime import datetime, date, time, timezone
import dateutil.parser
import networkx as nx
import matplotlib.pyplot as plt

def damp(cl):
    return 1-0.2*np.log10(cl+10)

def att_to_key(att, val):
    if att in ['acousticness','danceability','energy','instrumentalness','liveness', 'speechiness', 'valence']:
        return int(10*val)
    if att == 'loudness':
        return int(val/10)
    if att == 'tempo':
        return int(val/50)
    return val

def get_features(keys, sp, att):
    features = {}
    temp = []
    for id in keys:
        if(len(temp) == 50):
            ft = sp.audio_features(tracks=temp)
            for k in range(50):
                features[ft[k]['id']] = ft[k][att]
            temp.clear()
        temp.append(id)
    if(len(temp)>0):
        ft = sp.audio_features(tracks=temp)
        for k in range(len(temp)):
            features[ft[k]['id']] = ft[k][att]
        temp.clear()
    return features

class Graph(object):
    def __init__(self,graph_dict):
        self.graph_dict = graph_dict

    def nodes(self):
        """ returns the track ids within the graph """
        return list(self.graph_dict.keys())

    def names(self):
        items = []
        for id, node in self.graph_dict.items():
            items.append((id, node['name']))
        return items

    def get_weights(self, id, t):
        weights = {};
        tp = dateutil.parser.isoparse(t)
        for e in self.graph_dict[id]['edges']:
            ep = dateutil.parser.isoparse(e['t0'])
            weight = damp(e['cl'])*np.exp(-(1/(60*60*24*e['decay']))*(tp-ep).total_seconds())
            if e['id'] not in weights:
                weights[e['id']] = weight
            else:
                weights[e['id']] += weight
        return weights

    def get_weight(self, id1, id2, t):
        val = self.get_weights(id1,t)[id2]
        if val == None:
            return 0
        return val

    def node_stats(self, id, t, rel):
        weights = self.get_weights(id, t)
        degree = 0
        strength = 0
        #degree and popularity
        for k,v in weights.items():
            degree += 1
            strength += v
        #related songs
        sw = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
        related = []
        i=0
        for k in sw:
            if(i==rel): break
            related.append(self.graph_dict[k[0]]['name'])
            i+=1
        #put stats in dict
        stats = {"name": self.graph_dict[id]['name'], "deg": degree, "strength": strength, "related": related}
        return stats

    def strongest_k(self,k,t):
        values = []
        for id,v in self.graph_dict.items():
            values.append((id, v['name'], self.node_stats(id,t,0)['strength']))
        values.sort(key=lambda kv: kv[2], reverse=True)
        if k>len(values): k=len(values)
        return values[0:k]

    def export_dict(self):
        return self.graph_dict

class Song (Graph):
    """ bare-minimum graph_dict structure: {id: {'name', 'streams', 'edges':[...,{'id','cl','decay','t0'},...], 'artists': [...,{'id', 'name'},...]}}. """
    def __init__(self, graph_dict, cvalue, qvalue, decay = 60):
        if graph_dict == None:
            graph_dict = {}
        self.decay = decay #default decay rate
        self.cvalue = cvalue #these are not actually used yet
        self.qvalue = qvalue
        Graph.__init__(self,graph_dict)

    def add_track(self, track):
        """ track is a dictionary of format {'id','name'} """
        if track['id'] not in self.graph_dict:
            self.graph_dict[track['id']] = {'name': track['name'], 'streams':0, 'edges': [], "artists": []}
            for a in track["artists"]:
                # if(a['id']!=None):
                self.graph_dict[track['id']]["artists"].append({'id': a['id'], 'name': a['name']})

    def stream(self,track):
        self.graph_dict[track['id']]["streams"] += 1

    def add_edge(self, track1, track2, time, cl, decay = None):
        """ cl is context length (size of plyalist, listening radius). edge weight is inversely proportional to cl"""
        self.add_track(track1)
        self.add_track(track2)
        if decay == None:
            decay = self.decay
        # if track1['id'] == track2['id']: return
        self.graph_dict[track1['id']]['edges'].append({'id':track2['id'], 'cl': cl, 'decay': decay, 't0': time})

class Artist (Graph):
    def __init__(self, graph_dict):
        if graph_dict == None:
            graph_dict = {}
        sz = len(graph_dict)
        artist_dict = {}
        i=0
        for id, node in graph_dict.items():
            print("track:"+ str(i)+"/"+str(sz), end="\r")
            track1 = node
            for ar1 in track1["artists"][0:1]:
                aid = ar1["id"]
                if aid not in artist_dict:
                    artist_dict[aid] = {}
                    artist_dict[aid]["edges"] = []
                    artist_dict[aid]["streams"] = 0
                    artist_dict[aid]["name"] = ar1["name"]
                artist_dict[aid]["streams"] += track1["streams"]
                for e in track1["edges"]:
                    track2 = graph_dict[e['id']]
                    for ar2 in track2["artists"][0:1]:
                        # if(aid == ar2['id']): continue
                        ae = {'id': ar2['id'], 'cl': e['cl'],'decay': e['decay'],'t0': e['t0']}
                        artist_dict[aid]["edges"].append(ae)
            i+=1
        Graph.__init__(self,artist_dict)

class Attribute(Graph):
    def __init__(self, graph_dict, att, sp):
        if graph_dict == None:
            graph_dict = {}
        sz = len(graph_dict)
        dict = {}
        i=0
        features = get_features(graph_dict.keys(), sp, att)
        for id, node in graph_dict.items():
            track1 = node
            # print(sp.audio_features(tracks = id))
            att_id = att_to_key(att,features[id])
            if att_id not in dict:
                dict[att_id] = {}
                dict[att_id]['edges'] = []
                dict[att_id]['streams'] = 0
            dict[att_id]["streams"] += track1["streams"]
            for e in track1["edges"]:
                track2 = graph_dict[e['id']]
                eid = att_to_key(att,features[e['id']])
                # if(att_id == eid): continue
                ne = {'id': eid, 'cl':e['cl'],'decay': e['decay'],'t0': e['t0']}
                dict[att_id]["edges"].append(ne)
            i+=1
        Graph.__init__(self,dict)

class Genre(Graph):
    def __init__(self, artist_dict, sp):
        '''graph_dict is the output of the Artist graph dictionary'''
        if artist_dict == None:
            artist_dict = {}
        sz = len(artist_dict)
        dict = {}
        i=0
        genres = {}
        temp = []
        for id in artist_dict.keys():
            if(len(temp) == 50):
                artists = sp.artists(temp)
                for a in artists['artists']:
                    genres[a['id']] = a['genres']
                temp.clear()
            temp.append(id)
        if(len(temp)>0):
            artists = sp.artists(temp)
            for a in artists['artists']:
                genres[a['id']] = a['genres']
            temp.clear()
        for id, node in artist_dict.items():
            print("artist:"+ str(i)+"/"+str(sz), end="\r")
            for g in genres[id]:
                if g not in dict:
                    dict[g] = {}
                    dict[g]["edges"] = []
                    dict[g]["streams"] = 0
                dict[g]["streams"] += node["streams"]
                for e in node["edges"]:
                    for g2 in genres[e['id']]:
                        # if(g == g2): continue
                        ge = {'id': g2, 'cl': e['cl'],'decay': e['decay'],'t0': e['t0']}
                        dict[g]["edges"].append(ge)
            i+=1
        Graph.__init__(self,dict)

def enum_tracks(tracks):
    out = []
    for i, item in enumerate(tracks['items']):
        out.append(item)
        # print("   %d %32.32s %s" % (i, track['artists'][0]['name'].encode('utf-8'),
        #     track['name'].encode('utf-8')))
    return out

def within_session(item1, item2):
    if item1 == None: return False
    if item1["context"] and item2["context"]:
        if item1["context"]['uri'] == item2["context"]["uri"]: return True
    delta = dateutil.parser.isoparse(item1['played_at'])-dateutil.parser.isoparse(item2['played_at'])
    if delta.total_seconds() > 3*item1['track']['duration_ms']/1000: return False # if greater than two songs lengths paused between songs, they are in two distinct listening sessions
    return True

if __name__ == '__main__':

    scope = 'playlist-read-private user-library-read user-read-private user-read-email user-read-currently-playing user-read-recently-played user-read-playback-state'

    if len(sys.argv) > 1:
        users = sys.argv[1:]
    else:
        print("Usage: %s usernames" % (sys.argv[0],))
        sys.exit()

    for u in users:
        token = util.prompt_for_user_token(u,
                               scope,
                               client_id='8698031f9fa24db79f2074418f296b10',
                               client_secret='c2b602ae3ef1446f9d5164ca724ff318',
                               redirect_uri='http://localhost:8888/callback',
                               cache_path="tokens/.cache-"+u)
        if token:
            sp = spotipy.Spotify(auth=token)
            usid = sp.current_user()['id']
            config = True #if user graph has been configured
            try:
                with open("data/json/"+usid+'.json') as f:
                    datastore = json.load(f)
                    if datastore["valid"]: print("valid config file") #throws exception if key is nonexistent
            except:
                #initialize configuration dictionary
                config = False
                datastore = {"dict": {}, "decay": 10, "lradius": 5, "cvalue":1, "qvalue":1, "lastupdated": None}

            sg = Song(datastore["dict"], datastore["cvalue"], datastore["qvalue"], datastore["decay"])
            ctime = datetime.now(timezone.utc).isoformat()

            """ init song graph by looping through playlists """
            if config==False:
                playlists = sp.current_user_playlists()
                ctracks = []
                while playlists:
                    for playlist in playlists['items']:
                        if(playlist['name'] == 'Discover Archive'): continue
                        if playlist['owner']['id'] == usid:
                            # print(playlist['owner']['id'])
                            print(playlist['name'].encode('utf-8'))
                            # print ('  total tracks', playlist['tracks']['total'])
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
                                tr1 = ctracks[i]
                                if(tr1['track']['id'] == None): continue
                                print(tr1['track']['name'].encode('utf-8'))
                                for j in range(sz):
                                    tr2 = ctracks[j]
                                    if(tr2['track']['id'] == None): continue
                                    sg.add_edge(tr1['track'],tr2['track'],tr1['added_at'],sz,365*3)
                                sg.stream(tr1['track'])
                            ctracks.clear()

                    if playlists['next']:
                        playlists = sp.next(playlists)
                    else:
                        playlists = None

            results = sp.current_user_recently_played()
            sessions = []
            curr_sess = []
            last = None
            num_update = 0

            prev_updated = (datastore["lastupdated"] != None)
            if prev_updated: update_time = dateutil.parser.isoparse(datastore["lastupdated"])

            for i,item in enumerate(results['items']):
                track = item["track"]
                #print(track['name'] + ' - ' + track['artists'][0]['name'])
                #datetime.fromisoformat() not supported in Python <3.7
                if prev_updated:
                    stream_time = dateutil.parser.isoparse(item['played_at'])
                    if(update_time < stream_time): num_update+=1
                else:
                    num_update+=1

                if within_session(last, item):
                    #print(curr_sess[0]["track"]["name"])
                    curr_sess.append(item)
                    last = item
                else:
                    if last != None:
                        sessions.append(curr_sess.copy())
                        curr_sess.clear()
                    if prev_updated:
                        if(update_time > stream_time): break

                    curr_sess.append(item)
                    last = item

            print("songs updated: " + str(num_update))
            for i in range(len(sessions)):
                print("\n"+"session:" + str(i))
                sz = len(sessions[i])
                if(sz >= num_update):
                    for m in range(num_update):
                        sg.add_track(sessions[i][m]["track"])
                        sg.stream(sessions[i][m]["track"])
                        for n in range(num_update):
                            sg.add_edge(sessions[i][m]["track"], sessions[i][n]["track"],ctime,sz)
                    for m in range(num_update):
                        for n in range(num_update,sz):
                            sg.add_edge(sessions[i][m]["track"], sessions[i][n]["track"],ctime,sz)
                            sg.add_edge(sessions[i][n]["track"], sessions[i][m]["track"],ctime,sz)
                else:
                    for m in range(sz):
                        print(sessions[i][m]["track"]['name'].encode('utf-8'))
                        sg.add_track(sessions[i][m]["track"])
                        sg.stream(sessions[i][m]["track"])
                        for n in range(sz):
                            sg.add_edge(sessions[i][m]["track"], sessions[i][n]["track"],ctime,sz)
                    num_update -= sz

            datastore["dict"] = sg.export_dict()
            datastore["lastupdated"] = ctime
            datastore["valid"] = True

            with open("data/json/"+usid+'.json', 'w') as fp:
                json.dump(datastore, fp)
                print("saved succesfully")

        else:
            print("Can't get token for", u)
