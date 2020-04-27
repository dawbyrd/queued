from gen_data import Artist, Song, get_features
import json_to_nx
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
from matplotlib import pyplot as plt
from scipy.stats import norm
import user_sim
import codecs

def similar(G, name):
    names = nx.get_node_attributes(G, 'name')
    node = None

    for n in G.nodes():
        if(names[n].lower()[0:len(name)] == name.lower()):
            node = n
            break
    if(node == None):
        print("No '"+name+"' in graph.")
        return

    #edge weight wise
    print("based on weights")
    edges = sorted(G[node].items(), key = lambda e: e[1]['weight'], reverse = True)
    for i in range(10):
        print(names[edges[i][0]].encode('utf-8'),edges[i][1]['weight'])
    print()

    cos_sim = user_sim.gs2(G,node,1)
    #based on cosine similarity of edge vectors
    print("based on cosine similarity")
    values = sorted(cos_sim.items(), key = lambda kv: kv[1], reverse = True)
    for i in range(10):
        print(names[values[i][0]].encode('utf-8'),values[i][1])
    print()

    #composite
    print("composite of weight and cos similarity")
    values = sorted(G[node].items(), key = lambda e: e[1]['weight']*cos_sim[e[0]], reverse = True)
    for i in range(10):
        print(names[values[i][0]].encode('utf-8'),"{:e}".format(values[i][1]['weight']*cos_sim[values[i][0]]))

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

            sG, aG, gG = nx.read_gexf("data/gexf/S"+usid+".gexf"), nx.read_gexf("data/gexf/A"+usid+".gexf"), nx.read_gexf("data/gexf/G"+usid+".gexf")
            print("<<",u,">>")

            with codecs.open("out/"+usid+"-analysis.txt","w","utf-8") as f:
                f.write("Analysis for user: "+u+":\n\n")
                f.write("Pageranked Songs:\n")
                snames = nx.get_node_attributes(sG, 'name')
                streams = nx.get_node_attributes(sG, 'streams')
                spr = nx.pagerank(sG, weight='weight')
                spr = sorted(spr.items(), key = lambda nv: nv[1], reverse = True)
                for i in range(min(25,len(spr))):
                    f.write(snames[spr[i][0]]+" "+ str(spr[i][1]) +" " +str(streams[spr[i][0]])+"\n")
                f.write("\n")

                f.write("Pageranked Artists:\n")
                anames = nx.get_node_attributes(aG, 'name')
                streams = nx.get_node_attributes(aG, 'streams')
                apr = nx.pagerank(aG, weight='weight')
                apr = sorted(apr.items(), key = lambda nv: nv[1], reverse = True)
                for i in range(min(25,len(apr))):
                    f.write(anames[apr[i][0]]+" "+str(apr[i][1])+" "+str(streams[apr[i][0]])+"\n")
                f.write("\n")

                f.write("Pageranked Genres:\n")
                streams = nx.get_node_attributes(gG, 'streams')
                gpr = nx.pagerank(gG, weight='weight')
                gpr = sorted(gpr.items(), key = lambda nv: nv[1], reverse = True)
                for i in range(len(gpr)):
                    f.write(gpr[i][0]+" "+str(gpr[i][1])+" "+str(streams[gpr[i][0]])+"\n")

            continue

            for i in range(50):
                e = gG.edges(nbunch=[gpr[i][0]], data='weight')
                print(gpr[i][0], gpr[i][1], streams[gpr[i][0]])
                print(sorted(list(e), key = lambda e: e[2], reverse = True)[0:10])

            print("Pageranked Attribute:")
            vpr = nx.pagerank(vG, weight='weight')
            vpr = sorted(vpr.items(), key = lambda nv: nv[1], reverse = True)
            print(vpr)

            ### Getting PR vs. feature datapoints ###
            spr = nx.pagerank(sG, weight='weight')
            atts = ["acousticness", "instrumentalness", "energy", "tempo", "danceability", "speechiness"]
            groups = 6
            for a in atts:
                plt.figure()
                features = get_features(list(sG.nodes), sp, a)
                data = []
                xval = []
                means = []
                stds = []
                for id, value in features.items():
                    data.append((spr[id], value))
                data = sorted(data, key = lambda xy: xy[0])
                min = data[0][0]
                max = data[len(data)-1][0]
                curr = 0
                for i in range(groups):
                    yval = []
                    while(curr<len(data) and data[curr][0]<=min+(i+1)*(max-min)/groups):
                        yval.append(data[curr][1])
                        curr+=1
                    xval.append(min+(i+0.5)*(max-min)/groups)
                    mean,std=norm.fit(yval)
                    means.append(mean)
                    stds.append(std)

                x = [s[0] for s in data]
                y = [s[1] for s in data]

                ### Plotting Feature Data ###
                plt.plot(x, y, linestyle='None', marker='o',markerfacecolor=(0,0,1,0.2), markersize=6)
                plt.plot(xval, means, marker='o',markerfacecolor=(0.9,0.6,0.2,1), markersize=12)
                plt.plot(xval, np.subtract(means,stds), linestyle='None', marker="_",markerfacecolor=(0.9,0.6,0.2,1), markersize=12)
                plt.plot(xval, np.add(means,stds), linestyle='None', marker="_",markerfacecolor=(0.9,0.6,0.2,1), markersize=12)
                plt.ylabel(a)

            plt.show()

        else:
            print("Can't get token for", u)
