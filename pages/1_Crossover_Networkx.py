import streamlit as st
import pandas as pd
import networkx as nx
import numpy as np
from pyvis.network import Network
import streamlit.components.v1 as components
from matplotlib import pyplot
from matplotlib.colors import Normalize, to_rgba

# narrowed down: only edges with >100 count
edgelist_df_small = pd.read_csv("edgelist_df_small_fandoms.csv")
fandoms_small = pd.read_csv("fandoms_small.csv")
# create dict mapping of id to fandom cached_count for nodes
id_cached_count_mapping = dict(fandoms_small[['name', 'cached_count']].values)
# need to adjust cached_count because too big distance between numbers
adjusted_cached_count_mapping = {k: np.log1p(v) for k, v in id_cached_count_mapping.items()}


st.title("AO3 Fandom Cross-over Networks!")

st.subheader("Step 1: Choose your fandom")
default_fandom = "Haikyuu!!"
st.write("The network uses ", default_fandom, " as the default. It'll change as you search for your fandom and select it! There's lots of overlapping names for fandoms on AO3, so choose the one you're most interested in by hitting the checkbox in the leftmost column of the table.")

# SEARCH FANDOMS
user_search = st.text_input("Search for a fandom:")
if user_search:
    query = user_search
else:
    query = default_fandom

results_1 = edgelist_df_small[edgelist_df_small['name_1'].str.contains(query, case=False, na=False)][['count', 'integer_1', 'name_1']].rename(columns={"integer_1": "id", "name_1": "name"})
results_2 = edgelist_df_small[edgelist_df_small['name_2'].str.contains(query, case=False, na=False)][['count', 'integer_2', 'name_2']].rename(columns={"integer_2": "id", "name_2": "name"})
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
    ego_fandom = filtered_fandoms.iloc[event.selection['rows'][0]]['name']
    st.write(f"Great! You've chosen: **{ego_fandom}**")
else:
    ego_fandom = default_fandom
    st.write(f"No selection made. Network defaults to **{ego_fandom}**")

# SET RADIUS
st.subheader("Step 2: Set the radius")
col1, col2 = st.columns([3, 1])

with col1:
    st.write("The graph will include all neighbors of **distance <= radius**. Radius is limited from 2 to 5 for now. 1 would only show the single central node. **The bigger the number, the more nodes**, and the longer it takes to load!")
with col2:
    st.link_button("Ego graph documentation", "https://networkx.org/documentation/stable/reference/generated/networkx.generators.ego.ego_graph.html")

radius = st.select_slider("Select radius",
                          options=[2, 3, 4, 5],
                          )


st.subheader("Crossover network: " + ego_fandom + " with radius " + str(radius))
st.write("Hover over each node to learn more. Hover over an edge to find the number of crossovers between the two fandoms! Feel free to drag and zoom too.")
edgelist_df_small = edgelist_df_small.rename(columns={"count": "title"})
G_ego = nx.from_pandas_edgelist(edgelist_df_small, source='name_1', target='name_2', edge_attr='title')

# i want to color by cached_count of each fandom
nx.set_node_attributes(G_ego, name='cached_count', values=id_cached_count_mapping)
# need to adjust cached_count because too big distance between numbers
nx.set_node_attributes(G_ego, name='adjusted_cached_count', values=adjusted_cached_count_mapping)

# node attributes for degree 
degrees_all = dict(nx.degree(G_ego))
nx.set_node_attributes(G_ego, name='degree', values=degrees_all)
# Slightly adjust degree so that the nodes with very small degrees are still visible
number_to_adjust_by = 5
adjusted_node_size = dict([(node, degree+number_to_adjust_by) for node, degree in nx.degree(G_ego)])
nx.set_node_attributes(G_ego, name='size', values=adjusted_node_size)

# edge weights / distance: based on count
def custom_distance(u, v, edge_data):
    return edge_data['title'] * 0.01

# GRAPH: 
ego_graph = nx.ego_graph(G_ego, ego_fandom, radius=radius, distance=custom_distance)

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
color_attribute_list_normed = Normalize(vmin=3, vmax=max(color_attribute_list))
colormap = pyplot.get_cmap('Reds')
colors = [to_rgba(colormap(color_attribute_list_normed(value)), alpha = alpha_value) for value in color_attribute_list]
rgba_colors = [f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {alpha_value})' for r, g, b, _ in colors]
id_color_mapping = {key: color for key, color in zip(dict(ego_graph.nodes(data=True)).keys(), rgba_colors)}
nx.set_node_attributes(ego_graph, name='color', values=id_color_mapping)
nx.set_node_attributes(ego_graph, name='borderWidth', values=2)



# Initialize Pyvis Network
net = Network(notebook = True,
              width = '100%',height = '1000px',
              bgcolor ='#ebe9e1',font_color = 'black',
              neighborhood_highlight=True,
              cdn_resources='remote')
#ebe9e1
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
components.html(HtmlFile.read(), height=1000)