import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import numpy as np
import netviz
import complex2
import hist
import scatter4
import treemap2
import stackedbar
import pandas as pd
import urllib

#st.set_page_config(page_title="Writers Dashboard", page_icon="sfdc_cloud_icon_52.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

def main():
#	readme_text = st.expander("Not sure how to use the tool?", expanded=False)
#	with readme_text:
#		st.write("my explanation")
#add two expands, one for help and one for resources
	#st.header("Writer's Dashboard")
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/TotalOrganicKeywords-Jan2021vsJan2022.csv")
	app_mode = st.sidebar.selectbox("Check your content for:",
		['<select>', "Shared Content", "Linked Content", "Customer Search", "Freshness", "Comparison", "Complex Questions", "Beta"])
	if app_mode == "<select>":
		home()
		#readme_text.empty()
	elif app_mode == "Shared Content":
		#readme_text.empty()
		shared_content_page()
	elif app_mode == "Linked Content":
		#readme_text.empty()
		linked_content_page()
	elif app_mode == "Customer Search":
		#readme_text.empty()
		seo_page(df)
	elif app_mode == "Freshness":
		#readme_text.empty()
		freshness_page()
	elif app_mode == "Comparison":
		#readme_text.empty()
		comparison_page()
	elif app_mode == "Complex Questions":
		#readme_text.empty()
		complex_page()
	elif app_mode == "Beta":
		#readme_text.empty()
		test_page()

# THIS IS THE SECTION THAT CONTAINS UTILITY FUNCTIONS
# Download a single file and make its content available as a string.
@st.cache(show_spinner=False)
def get_file_content_as_string(path):
	url = 'https://raw.githubusercontent.com/tyrin/info-topo-dash/master/markdown/' + path
	response = urllib.request.urlopen(url)
	return response.read().decode("utf-8")
# THIS IS THE SECTION THAT RENDERS EACH PAGE
def home():
	st.sidebar.success("Select a visualization in the sidebar.")

	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use the Writer's Dashboard?"):
		readme_text = st.markdown(get_file_content_as_string("instructions.md"))
	with st.expander("Resources"):
		resource_text = st.markdown(get_file_content_as_string("resources.md"))

def shared_content_page():
	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use a Network Diagram?"):
		video_file = open('NetworkGraphHelpVid.mp4', 'rb')
		video_bytes = video_file.read()
		st.video(video_bytes)
		readme_text = st.markdown(get_file_content_as_string("sharedcontent.md"))
	st.subheader("Shared Content")
	ref='conref'
	#  clist = df['country'].unique()
	# country = st.selectbox("Select a country:",clist)
	netviz.main(ref)

def linked_content_page():
	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use a Network Diagram?"):
		video_file = open('NetworkGraphHelpVid.mp4', 'rb')
		video_bytes = video_file.read()
		st.video(video_bytes)
		readme_text = st.markdown(get_file_content_as_string("linkedcontent.md"))
	st.subheader("Linked Content")
	ref = 'xref'
	netviz.main(ref)

def seo_page(df):
	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use a Network Diagram?"):
#		video_file = open('NetworkGraphHelpVid.mp4', 'rb')
#		video_bytes = video_file.read()
#		st.video(video_bytes)
		readme_text = st.markdown(get_file_content_as_string("customersearch.md"))
	st.subheader("Customer Search and SEO")
	scattersearch = st.sidebar.radio(
	"Keyword search for:",
	('term', 'page'))
	scatterterm=""
	if len(scatterterm) == 0:
		scatterterm = 'no'
	scatterterm = st.sidebar.text_input('Enter a search term:', value="", max_chars=25)
	scattertermlc = scatterterm.lower()
	#st.write(scattertermlc)
	scatter4.matscatterplot3(scattertermlc, scattersearch)

def freshness_page():
	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use a Freshness Diagram?"):
#		video_file = open('NetworkGraphHelpVid.mp4', 'rb')
#		video_bytes = video_file.read()
#		st.video(video_bytes)
		readme_text = st.markdown(get_file_content_as_string("customersearch.md"))
	st.subheader("Freshness")
	#heat.main()
	hist.main()

def comparison_page():
	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use the Comparison Diagrams?"):
#		video_file = open('NetworkGraphHelpVid.mp4', 'rb')
#		video_bytes = video_file.read()
#		st.video(video_bytes)
		readme_text = st.markdown(get_file_content_as_string("customersearch.md"))
	st.subheader("Comparison")
	comparetype = st.sidebar.radio(
		"Select a visualization",
		('Reference Treemap', 'Portal Freshness'))
	if comparetype == "Reference Treemap":
		treemap2.main()

	elif comparetype == "Portal Freshness":
		stackedbar.comparebar()

def complex_page():
	# Render the readme as markdown using st.markdown.
	with st.expander("How Do I Use the Complex Network Diagram?"):
#		video_file = open('NetworkGraphHelpVid.mp4', 'rb')
#		video_bytes = video_file.read()
#		st.video(video_bytes)
		readme_text = st.markdown(get_file_content_as_string("customersearch.md"))
	st.subheader("Complex Questions")
	#st.write("This graph is complex and may take longer to load. If you encounter a blank screen, refresh your browser and try again.")
	ref = 'choose'
	complex2.main()

def test_page():
	st.subheader("Beta")
	st.write("No visualizations are currently in beta.")
	#barplotly.mainbar()
#Unique list of domains...?
#dlist = df['country'].unique()

if __name__ == "__main__":
	main()