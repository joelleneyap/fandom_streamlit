import streamlit as st
import pandas as pd
import networkx as nx
import numpy as np
from pyvis.network import Network
import streamlit.components.v1 as components
from matplotlib import pyplot
from matplotlib.colors import Normalize, to_rgba

st.title("The MCU Number Game")
st.write("*Inspired by [The Oracle of Bacon](https://oracleofbacon.org/help.php)*")
# narrowed down: only edges with >100 count
edgelist_df = pd.read_csv("edgelist_df_small_fandoms.csv")
fandoms_small = pd.read_csv("fandoms_small.csv")

G = nx.from_pandas_edgelist(edgelist_df, source='name_1', target='name_2', edge_attr='count') #, create_using=nx.MultiGraph()

# create dict mapping of ids to fandom names to secure node attributes
id_fandom_mapping = dict(fandoms_small[['id', 'name']].values)

# create dict mapping of id to fandom cached_count for nodes
id_cached_count_mapping = dict(fandoms_small[['name', 'cached_count']].values)

# need to adjust cached_count because too big distance between numbers
adjusted_cached_count_mapping = {k: np.log1p(v) for k, v in id_cached_count_mapping.items()}

def convert_int(d):
    # result = {}
    # Convert all values to Python int
    for key, value in d.items():
        if isinstance(value, np.int64):  # Check if the value is numpy.int64
            d[key] = int(value)  # Convert to Python int
    return d

id_fandom_mapping = convert_int(id_fandom_mapping)
id_cached_count_mapping = convert_int(id_cached_count_mapping)
adjusted_cached_count_mapping = convert_int(adjusted_cached_count_mapping)

# set node attribudes for fandom names
nx.set_node_attributes(G, name='fandom', values=id_fandom_mapping)

# i want to color by cached_count of each fandom
nx.set_node_attributes(G, name='cached_count', values=id_cached_count_mapping)

# need to adjust cached_count because too big distance between numbers
nx.set_node_attributes(G, name='adjusted_cached_count', values=adjusted_cached_count_mapping)

# node attributes for degree 
degrees_all = dict(nx.degree(G))
nx.set_node_attributes(G, name='degree', values=degrees_all)

# Slightly adjust degree so that the nodes with very small degrees are still visible
number_to_adjust_by = 10
adjusted_node_size = dict([(node, degree/number_to_adjust_by) for node, degree in nx.degree(G)])
nx.set_node_attributes(G, name='adjusted_node_size', values=adjusted_node_size)

# most well-connected
st.header("The Challenge:")
central_node = max(nx.eigenvector_centrality(G), key=nx.eigenvector_centrality(G).get)
st.write(f"The fandom included in the most number of crossovers in 2021 is the **{central_node}*.")
st.write("The MCU Number is the **smallest number of links a given fandom is away from the MCU**, if a link represents fics with a crossover between 2 fandoms. Most fandoms are connected to the MCU somehow — the average number of links away from the MCU is 1.46.")
st.write("Your challenge is to find a fandom with the **highest MCU Number**! Or one that has no crossovers with the MCU at all!")



default_fandom = "The Lord of the Rings - All Media Types"

# SEARCH FANDOMS
user_search = st.text_input("Search for a fandom:")
if user_search:
    query = user_search
else:
    query = default_fandom

results_1 = edgelist_df[edgelist_df['name_1'].str.contains(query, case=False, na=False)][['count', 'integer_1', 'name_1']].rename(columns={"integer_1": "id", "name_1": "name"})
results_2 = edgelist_df[edgelist_df['name_2'].str.contains(query, case=False, na=False)][['count', 'integer_2', 'name_2']].rename(columns={"integer_2": "id", "name_2": "name"})
filtered_fandoms = pd.concat([results_1, results_2], axis=0)
filtered_fandoms = filtered_fandoms.drop_duplicates(subset='id').drop(columns=['count'])
filtered_fandoms['cached_count'] = filtered_fandoms['name'].map(id_cached_count_mapping)
filtered_fandoms = filtered_fandoms.sort_values(by='cached_count', ascending=False)[['name', 'cached_count']].head()

column_configuration = {
        "name": st.column_config.TextColumn(
            "Fandom", 
            help="Fandom name", 
            max_chars=100, 
            width="medium"
        ),
        "cached_count": st.column_config.NumberColumn(
            "Count",
            help="Number of works under this fandom",
            width="medium"
        ),
    }
    
event = st.dataframe(
    filtered_fandoms,
    column_config=column_configuration,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",)

if len(event.selection['rows']) > 0:
    test_node = filtered_fandoms.iloc[event.selection['rows'][0]]['name']
    st.write(f"You've chosen: **{test_node}**")
else:
    test_node = default_fandom
    st.write(f"No selection made. Network defaults to **{test_node}**")





try:
    # Attempt to find the shortest path length between the two nodes
    path_length = nx.shortest_path_length(G, source=test_node, target=central_node)
    st.write(f"The shortest path between '{test_node}' and '{central_node}' has {path_length} edge(s).")
    st.info(f"The MCU number of {test_node} is **{path_length}**.", icon="🤯")

    ego_graph = G.subgraph(nx.shortest_path(G, test_node, central_node))

    # HOVER: NODE TITLE
    id_title_mapping = {}
    color_attribute_list = []
    color_by_this_attribute = 'adjusted_cached_count'

    for node, data in ego_graph.nodes(data=True):
        node_id = node
        degree = data.get('degree', 'N/A')
        cached_count = data.get('cached_count', 'N/A')
        adjusted_cached_count = data.get(color_by_this_attribute, 'N/A')
        # Create a plaintext string for the title
        title_str = f"Fandom: {node_id}\nDegree: {degree}\nCount: {cached_count}"
        id_title_mapping[node_id] = title_str
        color_attribute_list.append(adjusted_cached_count)
    nx.set_node_attributes(ego_graph, name='title', values=id_title_mapping)

    # HOVER: EDGE WEIGHT: done by switching weight name to title
    # COLOR: set within networkx before converting to pyvis net
    alpha_value = 0.9
    color_attribute_list_normed = Normalize(vmin=min(color_attribute_list), vmax=max(color_attribute_list))
    colormap = pyplot.get_cmap('Reds')
    colors = [to_rgba(colormap(color_attribute_list_normed(value)), alpha = alpha_value) for value in color_attribute_list]
    rgba_colors = [f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {alpha_value})' for r, g, b, _ in colors]
    id_color_mapping = {key: color for key, color in zip(dict(ego_graph.nodes(data=True)).keys(), rgba_colors)}
    nx.set_node_attributes(ego_graph, name='color', values=id_color_mapping)
    nx.set_node_attributes(ego_graph, name='borderWidth', values=2)

    # Initialize Pyvis Network
    net = Network(notebook = True,
                width = '100%',height = '500px',
                bgcolor ='white',font_color = 'black',
                #filter_menu=True, 
                cdn_resources='remote')
    net.from_nx(ego_graph)

    # Physics
    net.repulsion(
                node_distance=400,
                central_gravity=0.5,
                spring_length=110,
                spring_strength=0.10,
                damping=0.95
                )

    path = '/tmp'
    net.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')
    components.html(HtmlFile.read(), height=500)

except nx.NetworkXNoPath:
    # Handle the case where no path exists
    st.write(f"Nice one! No path exists between '{test_node}' and '{central_node}'.")
    st.balloons()