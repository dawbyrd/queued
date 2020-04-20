from gen_data import Artist, Song
import sys
import os
import json
import spotipy.util as util
import spotipy

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

if __name__ == '__main__':
    for filename in os.listdir("data/json"):
        with open("data/json/"+filename) as f:
            datastore = json.load(f)
            if(not datastore["valid"]): continue

            ctime = datastore["lastupdated"]

            sg = Song(datastore["dict"], datastore["cvalue"], datastore["qvalue"], datastore["decay"])
            ag = Artist(sg.export_dict())

            for title,g in {"song": sg, "artist": ag}.items():
                root = Element('gexf')
                root.set("xmlns", 'http://www.gexf.net/1.2draft')
                root.set("xmlns:xsi", 'http://www.w3.org/2001/XMLSchema−instance')
                root.set("xsi:schemaLocation", 'http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd')
                root.set("version", "1.2")

                meta = SubElement(root, 'meta')
                creator = SubElement(meta, 'creator')
                creator.text = 'Dawson Byrd'
                description = SubElement(meta, 'description')
                description.text = "Visualization of graph for user " + filename[:-5]

                graph = SubElement(root, 'graph')
                graph.set("defaultedgetype", "undirected")

                node_att = SubElement(graph, "attributes")
                node_att.set("class", "node")
                att1 = SubElement(node_att, "attribute")
                att1.set("id",str(0))
                att1.set("title","name")
                att1.set("type","string")

                att2 = SubElement(node_att, "attribute")
                att2.set("id",str(1))
                att2.set("title","streams")
                att2.set("type","integer")

                nodes = SubElement(graph, "nodes")
                edges = SubElement(graph, "edges")

                ecount = 0
                for id, item in g.export_dict().items():
                    node = SubElement(graph, "node")
                    node.set("id", id)
                    node.set("label", item["name"])
                    attvalues = SubElement(node, "attvalues")
                    attv1 = SubElement(attvalues, "attvalue")
                    attv1.set("for",str(0))
                    attv1.set("value",item["name"])

                    attv2 = SubElement(attvalues, "attvalue")
                    attv2.set("for",str(1))
                    attv2.set("value",str(item["streams"]))

                    weights = g.get_weights(id,ctime)
                    for id2 in weights:
                        edge = SubElement(edges, "edge")
                        edge.set("id", str(ecount))
                        edge.set("source", id)
                        edge.set("target", id2)
                        edge.set("weight", str(weights[id2]))
                        ecount += 1

                with open("data/gexf/"+filename[:-5]+"_"+title+".gexf", 'wb') as fp:
                    fp.write(prettify(root).encode("utf-8"))
                    print("saved succesfully")
