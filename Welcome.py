import streamlit as st
from st_social_media_links import SocialMediaIcons

st.set_page_config(
    page_title="AO3xNetworkX",
    page_icon="👋",
)

st.title("Welcome to the AO3xNetworkX project! 👋")

# st.sidebar.success()

st.write(
    """
    This project uses **Social Network Analysis on data from fanfiction website Archive of Our Own** in March 2021.
    It focuses on crossovers by drawing links between fandoms when they're tagged together in at least one hundred works, and plots graphs that visualize the interconnected relationships between fandoms and their communities.
    """
    )

st.subheader("Two Apps!")
st.page_link("pages/1_Crossover_Networkx.py", label=":blue-background[**1. Crossover Network**]", icon="🕸️")
st.write("Visualizes network of crossovers for one fandom of your choosing")

st.page_link("pages/2_MCU_Number.py", label=":blue-background[**2. The MCU Number Game**]", icon="🦹")
st.write("Try to find fandoms as far as possible from the central node!")

st.subheader("More Info")
st.write("This is made possible by AO3's [data dump for fan statisticians](https://archiveofourown.org/admin_posts/18804).")
st.write("If you'd like to learn more, I've documented this personal project [over here](https://joelleneyap.github.io/quartz/DSxAO3/) on Quartz.")

st.divider()
social_media_links = [
  "https://github.com/joelleneyap/fandom_streamlit",
  "https://twitter.com/hug_starved",
  "https://www.linkedin.com/in/joellene-yap/"
]
colors = ["#d6536d", "#d6536d", "#d6536d"]
social_media_icons = SocialMediaIcons(social_media_links, colors)
social_media_icons.render()
