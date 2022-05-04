import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import numpy as np
import netviz
import complex2
import hist
import Dist
import scatter
import scatter2
import treemap2
import stackedbar
import pandas as pd
st.set_page_config(layout="wide")

def main():
#	readme_text = st.expander("Not sure how to use the tool?", expanded=False)
#	with readme_text:
#		st.write("my explanation")
#add two expands, one for help and one for resources
	st.header("CCX Data Visualization")
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/TotalOrganicKeywords-Jan2021vsJan2022.csv")
	app_mode = st.sidebar.selectbox("Check your content for:",
		['<select>', "Shared Content", "Linked Content", "Relevance", "Freshness", "Comparison", "Complex Questions", "Beta"])
	if app_mode == "<select>":
		home()
		#readme_text.empty()
	elif app_mode == "Shared Content":
		#readme_text.empty()
		shared_content_page()
	elif app_mode == "Linked Content":
		#readme_text.empty()
		linked_content_page()
	elif app_mode == "Relevance":
		#readme_text.empty()
		relevance_page(df)
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

# THIS IS THE SECTION THAT RENDERS EACH PAGE
def home():
	st.sidebar.success("Select a visualization in the sidebar.")
	with st.expander("How Do I Use the Writer's Dashboard?"):
		st.write("""
			Information about usage.
		""")
	with st.expander("Resources"):
		st.write("""
			Resource Information
		""")

def shared_content_page():
	st.subheader("Shared Content")
	ref='conref'
	#  clist = df['country'].unique()
	# country = st.selectbox("Select a country:",clist)
	netviz.main(ref)

def linked_content_page():
	st.subheader("Linked Content")
	ref = 'xref'
	netviz.main(ref)

def relevance_page(df):
	st.subheader("Relevance")
	scattersearch = st.sidebar.radio(
	"Keyword search for:",
	('term', 'page'))
	scatterterm=""
	if len(scatterterm) == 0:
		scatterterm = 'no'
	scatterterm = st.sidebar.text_input('Enter a search term:', value="", max_chars=25)
	scatter2.matscatterplot3(scatterterm, scattersearch)

def freshness_page():
	st.subheader("Freshness")
	#heat.main()
	hist.main()

def comparison_page():
	st.subheader("Comparison")
	comparetype = st.sidebar.radio(
		"Select a visualization",
		('Reference Treemap', 'Portal Freshness'))
	if comparetype == "Reference Treemap":
		treemap2.main()

	elif comparetype == "Portal Freshness":
		stackedbar.comparebar()

def complex_page():
	st.subheader("Complex Questions")
	#st.write("This graph is complex and may take longer to load. If you encounter a blank screen, refresh your browser and try again.")
	ref = 'choose'
	complex2.main()

def test_page():
	st.subheader("Beta")
	st.write("This graph is complex and may take longer to load. ")
#Unique list of domains...?
#dlist = df['country'].unique()

if __name__ == "__main__":
	main()