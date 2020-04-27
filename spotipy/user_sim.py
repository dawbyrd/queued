import json_to_nx
import sys
import spotipy
import spotipy.util as util
import numpy as np
import networkx as nx
from scipy.stats import norm

client_id = '8698031f9fa24db79f2074418f296b10'
client_secret='c2b602ae3ef1446f9d5164ca724ff318'
redirect_uri='http://localhost:8888/callback'

graphs = {}

def softmax(x):
    return np.exp(x)/sum(np.exp(x))

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def gs1(G, g, sens):
    gw = softmax(sens*np.array(normalize([v['weight'] for v in G[g].values()])))
    return dict(zip(G[g].keys(),gw))

def gs2(G, g, sens):
    gw = normalize([v['weight'] for v in G[g].values()])
    gdict = dict(zip(G[g].keys(),gw))
    prods = []
    for n in G.nodes:
        nw = normalize([v['weight'] for v in G[n].values()])
        ndict = dict(zip(G[n].keys(),nw))
        prod = 0
        for x in ndict:
            if(x in gdict):
                prod += ndict[x] * gdict[x]
        prods.append(sens*prod)
    return dict(zip(G.nodes, softmax(prods)))

def combine(s1, s2, sens):
    s = {}
    for g in s1:
        if g in s2:
            s[g] = sens*s1[g]*s2[g]
    ns = dict(zip(s.keys(),softmax(list(s.values()))))
    return ns

def list_genres(G, num, sens1, sens2, sens3):
    # deg = np.average([n[1] for n in G.degree(G.nodes, weight='weight')])
    gpr = nx.pagerank(G, weight='weight')
    gpr = sorted(gpr.items(), key = lambda nv: nv[1], reverse = True)
    for i in range(num):
        print(gpr[i][0])
        sim1 = gs1(G1,gpr[i][0],sens1)
        sim2 = gs2(G1,gpr[i][0],sens2)
        print(sorted(sim1.items(), key = lambda kv: kv[1], reverse=True)[0:10])
        print(sorted(sim2.items(), key = lambda kv: kv[1], reverse=True)[0:10])
        print(sorted(combine(sim1,sim2,sens3).items(), key = lambda kv: kv[1], reverse=True)[0:10])

def kl_div(gpr1, gpr2, eps):
    miss = []
    for g in gpr1:
        if g not in gpr2:
            miss.append(g)
        else:
            gpr2[g] -= eps/len(gpr2)
    for g in miss:
        gpr2[g] = eps/len(miss)
    kl = {}
    for g in gpr1:
        kl[g] = gpr1[g]*np.log(gpr1[g]/gpr2[g])
    return kl

def bhat(gpr1, gpr2):
    sim = 0
    for g in gpr1:
        if g in gpr2:
            sim += np.sqrt(gpr1[g]*gpr2[g])
    return sim

def cosine_sim(gpr1, gpr2):
    gpr1_norm = normalize(list(gpr1.values()))
    gpr1 = dict(zip(gpr1.keys(),gpr1_norm))
    gpr2_norm = normalize(list(gpr2.values()))
    gpr2 = dict(zip(gpr1.keys(),gpr2_norm))
    sim = 0
    for g in gpr1:
        if g in gpr2:
            sim += gpr1[g]*gpr2[g]
    return sim

def complex_sim(gpr1, gpr2):
    sim = 0
    for g in gpr1:
        sum=0
        gsim1 = gs1(G1,g,20)
        gsim2 = gs2(G1,g,100)
        gs = combine(gsim1,gsim2,200)
        for h in gs:
            if h in gpr2:
                sum += gs[h]*gpr2[h]
        sim += gpr1[g]*sum
    return sim

def user_sim(id1,id2,type):
    if (type+id1) in graphs:
        G1 = graphs[type+id1]
    else:
        G1 = nx.read_gexf("data/gexf/"+type+id1+".gexf")
        graphs[type+id1] = G1
    if (type+id2) in graphs:
        G2 = graphs[type+id2]
    else:
        G2 = nx.read_gexf("data/gexf/"+type+id2+".gexf")
        graphs[type+id2] = G2
    gpr1 = nx.pagerank(G1, weight='weight')
    gpr2 = nx.pagerank(G2, weight='weight')

    kl = kl_div(gpr1,gpr2,0.0001)
    # for k in sorted(kl.items(), key = lambda kv: kv[1]):
    #     print(k[0],k[1])
    return {'kl': np.sum(list(kl.values())), 'bhat': bhat(gpr1,gpr2), 'cos': cosine_sim(gpr1,gpr2)}

def similarity(user1, user2, type):
    scope = 'playlist-read-private user-library-read user-read-private user-read-email user-read-currently-playing user-read-recently-played user-read-playback-state'
    t1 = util.prompt_for_user_token(user1, scope,client_id=client_id, client_secret=client_secret,redirect_uri=redirect_uri, cache_path="tokens/.cache-"+user1)
    t2 = util.prompt_for_user_token(user2, scope,client_id=client_id, client_secret=client_secret,redirect_uri=redirect_uri, cache_path="tokens/.cache-"+user2)
    if t1 and t2:
        sp1, sp2 = spotipy.Spotify(auth=t1), spotipy.Spotify(auth=t2)
        id1, id2 = sp1.current_user()['id'], sp2.current_user()['id']
        return user_sim(id1,id2,type)
    else:
        print("Can't get tokens for specified users")

def main(users):
    values = {}
    num = len(users)*len(users)
    i=0
    values['G']={}
    values['A']={}
    values['S']={}
    for a in users:
        for b in users:
            values['G'][(a,b)] = similarity(a,b,'G')
            values['A'][(a,b)] = similarity(a,b,'A')
            values['S'][(a,b)] = similarity(a,b,'S')
            print("progress:"+str(i)+"/"+str(num), end="\r")
            i+=1

    for type in ['S','A','G']:
        G = nx.MultiDiGraph()
        for k in values[type]:
            G.add_edge(k[0], k[1], weight=values[type][k]['kl'])
        nx.write_gexf(G, "data/gexf/"+type+"_user_graph.gexf")
    # sys.exit() #comment this out if want to print metrics for each pair

        pairs = sorted(values[type].items(), key = lambda kv: kv[1]['kl'])
        with open("out/"+type+"similarities.txt", "w") as f:
            for p in pairs:
                f.write(p[0][0]+" "+ p[0][1]+" "+str(p[1]['kl'])+"\n")
            rankings = {}
            for a in users:
                rankings[a] = 0
            for a in users:
                k=0
                for p in pairs:
                    if(a == p[0][0]):
                        rankings[p[0][1]] += k
                        k+=1
                        f.write(p[0][0]+" "+ p[0][1]+" "+str(p[1]['kl'])+"\n")
                f.write("\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print("Usage: %s usernames" % (sys.argv[0],))
