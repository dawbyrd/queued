for type in ['S','A','G']:
    G = nx.MultiDiGraph()
    for k in values[type]:
        G.add_edge(k[0], k[1], weight=values[type][k]['kl'])
    nx.write_gexf(G, "data/gexf/"+type+"_user_graph.gexf")
# sys.exit() #comment this out if want to print metrics for each pair

    pairs = sorted([type].items(), key = lambda kv: kv[1]['kl'])
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
