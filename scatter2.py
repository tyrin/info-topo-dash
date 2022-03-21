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
# Note Plotly express can't be included directly in streamlit, you have to render it as an html page and then read it in
# the same way you do with networkx visualizations.

	plt.style.use('seaborn-whitegrid')

	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/TotalOrganicKeywords-Jan2021vsJan2022.csv")

	# keyword filtering
	if scatterterm == 'no':
		dff = df

	elif  scattersearch=='page':
		dff = df.loc[(df['Page'].str.contains(scatterterm))]

	else:
		dff = df.loc[(df['Keyword'].str.contains(scatterterm))]

	dff['CustomerSearch'] = df['Keyword'] + "<br>Page: " + df['Page']

	scattertype = st.sidebar.radio(
		"Select a Visualization",
		('Blended Rank', 'Blended Rank Change'))
	if scattertype == "Blended Rank":
		fig = px.scatter(dff, x="Blended Rank", y="Search Volume",
			text="CustomerSearch",
			log_x=True,
			size="Blended Rank",
			color="Blended Rank Change",
			size_max=25)
		#fig.update_traces(textposition='top center')
		fig.update_traces(mode="markers")
		fig.update_layout(
	    	height=800,
	    	title_text='Blended Rank and Search Volume'
		)

	elif scattertype == "Blended Rank Change":
		fig = px.scatter(dff, x="Blended Rank Change", y="Search Volume",
			text="CustomerSearch",
			log_x=True,
			size="Blended Rank",
			color="Search Volume",
			size_max=25)

			#fig.update_traces(textposition='top center')
		fig.update_traces(mode="markers")
		fig.update_layout(
			height=800,
			title_text='Blended Rank Change and Search Volume'
		)


	#fig.show()
	fig.write_html("scatter.html")
	HtmlFile = open("scatter.html", 'r', encoding='utf-8')
	source_code = HtmlFile.read()
	components.html(source_code, height = 700,width=900)
	st.dataframe(dff)
	@st.cache
	def convert_df(dff):
	   return dff.to_csv().encode('utf-8')

	csv = convert_df(dff)

	st.download_button(
	   "Press to Download",
	   csv,
	   "file.csv",
	   "text/csv",
	   key='download-csv'
	)
	#fig2.write_html("scatter.html")
