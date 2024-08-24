import streamlit as st
import pandas as pd
import networkx as nx
import numpy as np
from pyvis.network import Network



st.title("🎈 Test?")
st.write(
    "Let's start building! WOah."
)

# narrowed down: only edges with >100 count
edgelist_df_small = pd.read_csv("edgelist_df_small_fandoms.csv")
fandoms_small = pd.read_csv("fandoms_small.csv")

# create dict mapping of ids to fandom names to secure node attributes
id_fandom_mapping = dict(fandoms_small[['id', 'name']].values)
# create dict mapping of id to fandom cached_count for nodes
id_cached_count_mapping = dict(fandoms_small[['id', 'cached_count']].values)
# need to adjust cached_count because too big distance between numbers
adjusted_cached_count_mapping = {k: np.log1p(v) for k, v in id_cached_count_mapping.items()}

G_ego = nx.from_pandas_edgelist(edgelist_df_small, source='integer_1', target='integer_2', edge_attr='count')

# set node attribudes for fandom names
nx.set_node_attributes(G_ego, name='fandom', values=id_fandom_mapping)
# i want to color by cached_count of each fandom
nx.set_node_attributes(G_ego, name='cached_count', values=id_cached_count_mapping)
# need to adjust cached_count because too big distance between numbers
nx.set_node_attributes(G_ego, name='adjusted_cached_count', values=adjusted_cached_count_mapping)
# node attributes for degree 
degrees_all = dict(nx.degree(G_ego))
nx.set_node_attributes(G_ego, name='degree', values=degrees_all)
# Slightly adjust degree so that the nodes with very small degrees are still visible
number_to_adjust_by = 10
adjusted_node_size = dict([(node, degree/number_to_adjust_by) for node, degree in nx.degree(G_ego)])
nx.set_node_attributes(G_ego, name='adjusted_node_size', values=adjusted_node_size)

# edge weights / distance
nx.set_edge_attributes(G_ego, nx.get_edge_attributes(G_ego, 'count'), 'weight')
def custom_distance(u, v, edge_data):
    return edge_data['weight'] * 0.01


# GRAPH: CHOOSE EGO FANDOM
ego_fandom = 65
ego_graph = nx.ego_graph(G_ego, ego_fandom, radius=2, distance=custom_distance)
degrees_ego = dict(nx.degree(G_ego))

# Initialize Pyvis Network
net = Network(notebook=True, height="750px", width="100%", bgcolor="white", font_color="black", cdn_resources='in_line')

# Set the layout
pos_ego = nx.circular_layout(ego_graph, scale=1, center=(0, 0))
net.repulsion(node_distance=420, central_gravity=0.33, spring_length=110, spring_strength=0.10, damping=0.95)

ego_graph_limited = ego_graph.subgraph(list(ego_graph.nodes())[:50])

# Check the number of nodes and edges
print(f"Number of nodes in ego graph: {ego_graph.number_of_nodes()}")
print(f"Number of edges in ego graph: {ego_graph.number_of_edges()}")

# Precompute values outside the loop
sizes = {node: data['adjusted_node_size'] for node, data in ego_graph_limited.nodes(data=True)}
fandom_name = {node: data['fandom'] for node, data in ego_graph_limited.nodes(data=True)}
colors = {node: 'red' if node == ego_fandom else 'black' for node in ego_graph_limited.nodes()}




# Add nodes with attributes
for node, data in ego_graph_limited.nodes(data=True):
    size = adjusted_node_size[node]  # Adjust node size
    # color = colors[node]  # Ego node color vs others
    title = id_fandom_mapping[node]
    net.add_node(node, label=data['fandom'], title=title, size=size)

# Add edges with weights
for source, target, data in ego_graph_limited.edges(data=True):
    net.add_edge(source, target, value=data['count'])

# net.prep_notebook()
net.show("net.html")
# display(HTML('net.html'))

path = '/tmp'
net.save_graph(f'{path}/g.html')
HtmlFile = open(f'{path}/g.html', 'r', encoding='utf-8')