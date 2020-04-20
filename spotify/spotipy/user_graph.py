import json_to_nx
import user_sim
import sys
import spotipy
import spotipy.util as util
import numpy as np
import networkx as nx
from scipy.stats import norm

if __name__ == '__main__':
    with open("user_list.txt") as f:
        users = f.readline().split(" ")
    dists = user_sim.main(users)
    G = nx.MultiDiGraph()
    for k in dists:
        G.add_edge(k[0], k[1], weight=dists[k])

    for user in G.nodes():
