import json_to_nx
import user_sim
import sys
import spotipy
import spotipy.util as util
import numpy as np
import networkx as nx
from scipy.stats import norm
from itertools import chain, combinations

G = None

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(2,len(s)+1))

def get_rankings():
    stats = {}
    for user in G.nodes():
        avg1 = 0 #distance from others
        avg2 = 0 #distance from user
        n = len(G[user])
        for u in G[user]:
            # print(user, u, G[user][u][0]['weight'])
            # print(u, user, G[u][user][0]['weight'])
            avg1 += G[u][user]['weight']
            avg2 += G[user][u]['weight']
        avg1 /= n
        avg2 /= n
        stats[user] = [avg1, avg2, avg2-avg1, avg2/avg1]

    print("ranked by others->user:")
    for kv in sorted(stats.items(), key = lambda kv: kv[1][0]):
        print(kv[0], kv[1][0])
    print()
    print("ranked by user->others:")
    for kv in sorted(stats.items(), key = lambda kv: kv[1][1], reverse=True):
        print(kv[0], kv[1][1])
    print()
    print("ranked by ratio of user->others to others->user:")
    for kv in sorted(stats.items(), key = lambda kv: kv[1][3], reverse=True):
        print(kv[0], kv[1][3])
    print()
    print("ranked by difference between user->others and others->user:")
    for kv in sorted(stats.items(), key = lambda kv: kv[1][2], reverse=True):
        print(kv[0], kv[1][2])

def shortest_path(a,b):
    '''returns shortest path from a to b excluding traversing along (a,b). effectively returns a user that acts as a bridge from A to B'''
    H = G.copy()
    H.remove_edge(a,b)
    print(nx.shortest_path(H,a,b,weight='weight'))

def common(users):
    min = {'user': '', 'sum': np.inf}
    for u in G.nodes():
        sum=0
        if u in users: continue
        for v in users:
            sum += G[v][u]['weight']
        if sum < min['sum']:
            min['user'] = u
            min['sum'] = sum
    return min['user']

#the function below runs in O(2^n)
def best_groups(users):
    groups = {}
    for i in range(2,len(users)+1):
        sets = combinations(users, i)
        for s in sets:
            if i==2:
                groups[s] = (G[s[0]][s[1]]['weight']+G[s[1]][s[0]]['weight'])/2
            else:
                sum = 0
                for u in s[:-1]:
                    sum += (G[u][s[-1]]['weight']+ G[s[-1]][u]['weight'])
                groups[s] = (groups[s[:-1]]*(i-1)*(i-2)+sum)/(i*(i-1))

    return sorted(groups.items(), key = lambda kv: kv[1])

if __name__ == '__main__':
    G = nx.read_gexf("data/gexf/user_graph.gexf")
    # get_rankings(G)
    # for a in G.nodes():
    #     for b in G.nodes():
    #         if a==b: continue
    #         print(a,b,common([a,b]))
    for i,g in enumerate(best_groups(G.nodes())):
        print(i+1,g[0],g[1],common(g[0]))
