#run from app.py
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import pandas as pd
import plotly.express as px

#GRAPH WITHOUT LABELS----------------------------------------------
def matscatterplot3(scatterterm, scattersearch):

#GRAPH WITHOUT LABELS----------------------------------------------

	plt.style.use('seaborn-whitegrid')

	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/TotalOrganicKeywords-Jan2021vsJan2022.csv")

	# keyword filtering
	if scatterterm == 'no':
		dff = df

	elif  scattersearch=='page':
		dff = df.loc[(df['Page'].str.contains(scatterterm))]

	else:
		dff = df.loc[(df['Keyword'].str.contains(scatterterm))]


#PLOTLY with ANNOTATION------------------------------------------------

	plt.style.use('seaborn-whitegrid')

	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/TotalOrganicKeywords-Jan2021vsJan2022.csv")

	# keyword filtering
	if scatterterm == 'no':
		dff = df

	elif  scattersearch=='page':
		dff = df.loc[(df['Page'].str.contains(scatterterm))]

	else:
		dff = df.loc[(df['Keyword'].str.contains(scatterterm))]

	keywords = dff['Keyword']
	ranks = dff['Blended Rank']
	rankchanges = dff['Blended Rank Change'].astype(float)
	pages = dff['Page']
	searchvolumes = dff['Search Volume']
	categories = dff['Category']
	max_elements = dff['Keyword'].size
	# Search Terms by Search Volume and Rank Change with Size as Rank
	rng = np.random.RandomState(0)
	x = rankchanges
	y = searchvolumes
	fig = plt.figure(figsize=(10, 6))

	colors = rng.rand(max_elements)
	sizes = ranks * 20
	plt.gca().invert_yaxis()

	plt.scatter(x, y,
		c=colors,
		s=sizes,
		alpha=0.3,
		cmap='viridis')
	plt.colorbar();  # show color scale
	plt.xlabel("Blended Rank Changes")
	plt.ylabel("Search Volume")
	#change the caption if you add a search term
	if scatterterm == "":
		st.caption("Search Terms by Search Volume and Rank Change")
	else:
		caption = "Search Terms by Search Volume and Rank Change for " + scatterterm
		st.caption(caption)

	st.pyplot(fig)

# Search Terms by Search Volume and Rank With Size as Rank
	rng = np.random.RandomState(0)
	x = ranks
	y = searchvolumes
	fig2 = plt.figure(figsize=(10, 6))
	colors = rng.rand(max_elements)
	sizes = ranks * 20
	plt.gca().invert_yaxis()
	plt.scatter(x, y, c=colors, s=sizes, alpha=0.3,
            cmap='plasma')
	plt.colorbar();  # show color scale
	plt.xlabel("Blended Rank Changes")
	plt.ylabel("Search Volume")
#change the caption if you add a search term
	if scatterterm == "":
		st.caption("Search Terms by Search Volume and Rank Change")
	else:
		caption = "Search Terms by Search Volume and Rank Change for " + scatterterm
		st.caption(caption)
	st.pyplot(fig2)
	st.dataframe(dff)
# GRAPH WITH ANNOTATIONS----------------------------------------------------------VERSION4

	#The package contains eight color scales: “viridis”, the primary choice, and five alternatives with similar properties - “magma”, “plasma”, “inferno”, “cividis”, “mako”, and “rocket” -, and a rainbow color map - “turbo”.