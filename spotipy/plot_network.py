import matplotlib.pyplot as plt
import networkx as nx
import os
import numpy as np
import json_to_nx
import sys

if __name__ == '__main__':

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        type = sys.argv[2]
    else:
        print("Usage: %s 'JSON filename'" % (sys.argv[0],))
        sys.exit()

    G = json_to_nx.main([filename, type])[0]
    pos = nx.random_layout(G)
    plt.figure(figsize=(9,7))
    pr = nx.pagerank(G, weight='weight')
    scores = list(pr.values())
    avg = np.average(scores)
    max_pr = np.max(scores)
    print(len(scores))

    sizes = 800/(1+np.exp(-np.power(10,3.5)*(scores-(avg+max_pr)/2)))
    alphas = 1/(1+np.exp(-0.2*(scores-avg/3)))

    weights = [i[2] for i in list(G.edges(data='weight'))]
    w_avg = np.average(weights)
    max_w = np.max(weights)
    sens = 4# use sens=3 when plotting song graph, sens=2 when plotting genres
    op = 1

    names = nx.get_node_attributes(G, 'name')
    sort = sorted(pr.items(), key = lambda nv: nv[1], reverse = True)
    i=0
    for i in range(len(sort)):
        if(i>=100): names[sort[i][0]] = ""
        if(i<100):
            edges = list(G.edges(nbunch=[sort[i][0]], data='weight'))
            for e in edges:
                s_alpha = 1/(1+np.exp(-np.power(10,3.5)*((pr[e[0]]+pr[e[1]])/2-(avg+max_pr)/2)))
                w_alpha = 1/(1+np.exp(-25*(e[2]-(2*w_avg+max_w)/3)))
                print(str(s_alpha), str(w_alpha), str(i) +"/"+str(100), end="\r")
                alpha = np.power(s_alpha,2)*np.power(w_alpha,2)
                nx.draw_networkx_edges(G, pos, edgelist=[e[0:2]], alpha=alpha, width=1, edge_color = '#224C98')
                # nx.draw_networkx_edges(G, pos, edgelist=[e[0:2]], alpha=op*opac[i]/mopac, width=1, edge_color = (0,1,1))
    nx.draw_networkx_labels(G,pos,labels=names,font_size=5)
    nx.draw_networkx_nodes(G,pos,nodelist = nx.nodes(G), node_size = sizes, alpha = alphas)
    
    # opac = []
    # for i in range(len(edges)):
    #     e = []
    #     e.append(edges[i])
    #     print(str(nalpha), str(ealphas[i]), (str(i) +"/"+str(len(edges))), end="\r")
    #     opac.append(np.power(nalpha,sens)*np.power(ealphas[i],0))
    # mopac = max(opac)
    # for i in range(len(edges)):
    #     e = []
    #     e.append(edges[i])
    #     print(mopac, end="\r")
    #     if(op*opac[i]/mopac>0.05):
    #         print(mopac, (str(i) +"/"+str(len(edges))), end="\r")

    plt.show()
