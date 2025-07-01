from rdflib import Graph, Namespace, RDF
import networkx as nx
from pyvis.network import Network

from matplotlib import cm
import random

class NetworkGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_types = {}


class OntoVis:
    """ object to query and visualize ontologies as a graph in an html file. Warning, only rdf/xml formats are supported for now"""

    def __init__(self, ontologies_pathes = [], color_map_instance = {}):
        # Load ontology
        global_graph = Graph()
        for path in ontologies_pathes:
            global_graph.parse(path)  # or .ttl, .rdf
        self.global_graph = global_graph
        self.color_map_instance = color_map_instance


    def get_sparql_query(self, query):
        return self.global_graph.query(query)
    

    def build_network_graph(self, query  ):
        query_results = self.get_sparql_query(query)
        #build the graph
        netwrk_graph = NetworkGraph()

        for row in query_results:
            subj_uri = row.subject
            pred_uri = row.predicate  # now valid
            obj_uri = row.object      # note just one object variable now

            subj = OntoVis.short(str(subj_uri))
            pred = OntoVis.short(str(pred_uri))
            obj = OntoVis.short(str(obj_uri))
            # Get and save subject type if not already done
            if subj not in netwrk_graph.node_types:
                netwrk_graph.node_types[subj] = self.get_node_type(subj_uri)

            # Add edge and set object type
            netwrk_graph.graph.add_edge(subj, obj, label=pred)
            if obj not in netwrk_graph.node_types:
                netwrk_graph.node_types[obj] = self.get_node_type(obj_uri)

        return netwrk_graph

    
    def generate_html_from_network_graph(self, query, output_html_path="full_ontology_graph1.html", **kwargs):
        network_graph = self.build_network_graph(query)

        # Default rendering params
        node_size = kwargs.get("node_size", 35)
        node_shape = kwargs.get("node_shape", "dot")
        edge_font_size = kwargs.get("edge_font_size", 10)
        edge_color = kwargs.get("edge_color", None)  # optional
        edge_length = kwargs.get("edge_length", 250)
        edge_arrows = kwargs.get("edge_arrows", "to")
        net_height = kwargs.get("net_height", "700px")
        net_width = kwargs.get("net_width", "100%")
        directed = kwargs.get("directed", True)
        max_label_length = kwargs.get('max_label_length', 7)

        node_font_size = kwargs.get("edge_length", 12)
        node_font_color = kwargs.get("edge_length", "#000000")
        node_font_location = kwargs.get("edge_length", -65)

        node_font = kwargs.get("node_font", {"size": node_font_size, "color": node_font_color, "face": "arial", "vadjust": node_font_location})


        net = Network(height=net_height, width=net_width, directed=directed)

        # Customize physics options
        net.set_options("""
        var options = {
        "physics": {
            "enabled": true,
            "barnesHut": {
            "gravitationalConstant": -8000,
            "centralGravity": 0.3,
            "springLength": 300,
            "springConstant": 0.04,
            "damping": 0.09,
            "avoidOverlap": 1
            },
            "minVelocity": 0.75
        },
        "edges": {
            "smooth": {
            "type": "continuous"
            }
        }
        }
        """)


        for node in network_graph.graph.nodes():
            node_type = network_graph.node_types.get(node, "Unknown")
            color = self.get_color_for_class(node_type)
            net.add_node(
                node,
                label=OntoVis.format_label(node, max_label_length),
                shape=node_shape,
                size=node_size,
                color=color,
                font=node_font
            )

        for src, tgt, data in network_graph.graph.edges(data=True):
            net.add_edge(
                src,
                tgt,
                label=data.get("label", ""),
                arrows=edge_arrows,
                font={"size": edge_font_size},
                length=edge_length,
                color=edge_color
            )

        net.write_html(output_html_path)


    def generate_html_from_network_graph_obs(self, query, ouput_html_path = "full_ontology_graph1.html", ):        
        network_graph = self.build_network_graph(query)

        # Visualize
        net = Network(height="700px", width="100%", directed=True)
        for node in network_graph.graph.nodes():
            node_type = network_graph.node_types.get(node, "Unknown")
            color = self.get_color_for_class(node_type)
            net.add_node(
                node,
                label=node,
                shape="dot",
                size=35,
                color=color,
                font={
                    "size": 12,
                    "color": "#000000" ,
                    "face": "arial",
                    "vadjust": -50  # center the label vertically
                }
            )

        for src, tgt, data in network_graph.graph.edges(data=True):
            net.add_edge(
                src,
                tgt,
                label=data.get("label", ""),
                arrows="to",
                font={"size": 10},
                length=250
            )

        net.write_html(ouput_html_path)    


    def get_node_type(self, uri ):
        g = self.global_graph
        types = set()
        for _, _, o in g.triples((uri, RDF.type, None)):
            _type = OntoVis.short(str(o))
            if _type != 'NamedIndividual':
                types.add(_type)
        if types:
            # Return first type or combine multiple if needed
            return list(types)[0]
        else:
            return "Unknown"
        
    def get_color_for_class(self, _cls):
        if _cls not in self.color_map_instance:
            self.color_map_instance[_cls] = f'#{random.randint(0, 0xFFFFFF):06x}'
        return self.color_map_instance[_cls]
    
    
    @staticmethod
    def short(uri):
        if uri is None:
            return "Unknown"
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

    @staticmethod
    def format_label(label, max_length):
        parts = label.split('_')
        result = []
        current_length = 0
        current_chunk = []

        for part in parts:
            # +1 for the underscore that will be added back (except first word)
            additional_length = len(part) + (1 if current_chunk else 0)

            if current_length + additional_length > max_length and current_chunk:
                # Join the current chunk with '_', append to result
                result.append('_'.join(current_chunk))
                # Start a new chunk with the current part
                current_chunk = [part]
                current_length = len(part)
            else:
                current_chunk.append(part)
                current_length += additional_length

        # Append the last chunk
        if current_chunk:
            result.append('_'.join(current_chunk))


        return '\n'.join(result)

