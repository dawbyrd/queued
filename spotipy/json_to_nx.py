from gen_data import Artist, Song, Attribute, Genre, damp
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

# def remove_multi_edge(g):
#     H = nx.Graph()
#     for u,v,d in g.edges(data=True):
#         w = d['weight']
#         print(u,v,d)
#         if H.has_edge(u,v):
#             H[u][v]['weight'] += w
#             print(H[u][v]['weight'])
#         else:
#             H.add_edge(u,v,weight=w)
#     return H

def main(args):
    filename = args[0]
    types = args[1:]
    with open("data/json/"+filename) as f:
        datastore = json.load(f)

    ctime = datetime.now(timezone.utc).isoformat()
    tp = dateutil.parser.isoparse(ctime)
    g = Song(datastore["dict"], datastore["cvalue"], datastore["qvalue"], datastore["decay"])
    sgd = g.export_dict()
    result = []

    client_credentials_manager = SpotifyClientCredentials(client_id='8698031f9fa24db79f2074418f296b10', client_secret='c2b602ae3ef1446f9d5164ca724ff318')
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    for t in types:
        if(t=='song'):
            G = nx.Graph()
            sz = len(sgd)
            atts = [{},{},{}]
            i=0
            for id, value in sgd.items():
                j=0
                atts[0][id] = value['name']
                atts[1][id] = value['artists'][0]['name']
                atts[2][id] = value['streams']
                for e in value["edges"]:
                    # if(id == e['id']): continue
                    print('node:'+str(i)+"/"+str(sz),'edge:'+str(j)+"/"+str(len(value['edges'])), end='\r')
                    ep = dateutil.parser.isoparse(e['t0'])
                    weight = damp(e['cl'])*np.exp(-(1/(60*60*24*e['decay']))*(tp-ep).total_seconds())
                    if not G.has_edge(id,e['id']):
                        G.add_edge(id, e['id'], weight=0)
                    G[id][e['id']]['weight'] += weight
                    j+=1
                i+=1
            nx.set_node_attributes(G, atts[0], "name")
            nx.set_node_attributes(G, atts[1], "artist")
            nx.set_node_attributes(G, atts[2], "streams")
            result.append(G)
        elif(t == 'artist'):
            g = Artist(sgd)
            gd = g.export_dict()
            G = nx.Graph()
            sz = len(gd)
            atts = [{},{}]
            i=0
            for id, value in gd.items():
                j=0
                atts[0][id] = value['name']
                atts[1][id] = value['streams']
                for e in value["edges"]:
                    # if(id == e['id']): continue
                    print('node:'+str(i)+"/"+str(sz),'edge:'+str(j)+"/"+str(len(value['edges'])), end='\r')
                    ep = dateutil.parser.isoparse(e['t0'])
                    weight = damp(e['cl'])*np.exp(-(1/(60*60*24*e['decay']))*(tp-ep).total_seconds())
                    if not G.has_edge(id,e['id']):
                        G.add_edge(id, e['id'], weight=0)
                    G[id][e['id']]['weight'] += weight
                    j+=1
                i+=1
            nx.set_node_attributes(G, atts[0], "name")
            nx.set_node_attributes(G, atts[1], "streams")
            result.append(G)
        elif(t == 'genre'):
            g = Artist(sgd)
            gd = g.export_dict()
            g = Genre(gd,sp)
            gd = g.export_dict()
            G = nx.Graph()
            sz = len(gd)
            atts = [{},{}]
            i=0
            for id, value in gd.items():
                j=0
                atts[0][id] = value['streams']
                atts[1][id] = id
                for e in value["edges"]:
                    # if(id == e['id']): continue
                    print('node:'+str(i)+"/"+str(sz),'edge:'+str(j)+"/"+str(len(value['edges'])), end='\r')
                    ep = dateutil.parser.isoparse(e['t0'])
                    weight = damp(e['cl'])*np.exp(-(1/(60*60*24*e['decay']))*(tp-ep).total_seconds())
                    if not G.has_edge(id,e['id']):
                        G.add_edge(id, e['id'], weight=0)
                    G[id][e['id']]['weight'] += weight
                    j+=1
                i+=1
            nx.set_node_attributes(G, atts[0], "streams")
            nx.set_node_attributes(G, atts[1], "name")
            result.append(G)
        else:
            g = Attribute(sgd,t,sp)
            G = nx.Graph()
            gd = g.export_dict()
            sz = len(gd)
            i=0
            for id, value in gd.items():
                j=0
                for e in value["edges"]:
                    # if(id == e['id']): continue
                    print('node:'+str(i)+"/"+str(sz),'edge:'+str(j)+"/"+str(len(value['edges'])), end='\r')
                    ep = dateutil.parser.isoparse(e['t0'])
                    weight = damp(e['cl'])*np.exp(-(1/(60*60*24*e['decay']))*(tp-ep).total_seconds())
                    if not G.has_edge(id,e['id']):
                        G.add_edge(id, e['id'], weight=0)
                    G[id][e['id']]['weight'] += weight
                    j+=1
                i+=1
            result.append(G)

    return result

if __name__ == '__main__':
    main(sys.argv[1:])
