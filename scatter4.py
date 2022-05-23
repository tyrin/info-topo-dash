#run from app.py this has additional data for combined keyword and search volume across portals. However, is not working.
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import pandas as pd
import plotly.express as px

#GRAPH WITHOUT LABELS----------------------------------------------
#keyword filtering
message = st.empty()
def filterterm(df, scatterterm, scattersearch):
	if scatterterm == 'no':
		message.text("Select a visualization and enter a search term.")
		dff = df
		#st.dataframe(dff)
	elif  scattersearch=='volume':
		dff = df.loc[(df['Keyword'].str.contains(scatterterm))]
		# changing the Volume column from text to numeric so we can sort and use a color scale
		dff['Volume'] = pd.to_numeric(dff['Volume'])
	elif  scattersearch=='page':
		dff = df.loc[(df['Page'].str.contains(scatterterm))]
		#add a new column with the text for hover
		dff['CustomerSearch'] = df['Keyword'] + "<br>Page: " + df['Page']
		#st.dataframe(dff)
	else:
		dff = df.loc[(df['Keyword'].str.contains(scatterterm))]
		dff['CustomerSearch'] = df['Keyword'] + "<br>Page: " + df['Page']
	# if the term has no results, tell them and use the full data frame
	return dff

def matscatterplot3(scatterterm, scattersearch):
	if len(scatterterm) == 0:
		scatterterm = 'no'
#GRAPH WITHOUT LABELS----------------------------------------------
	scattertype = st.sidebar.radio(
		"Select a Visualization",
		('Blended Rank', 'Blended Rank Change', 'Combined Keyword'))
# Note Plotly express can't be included directly in streamlit, you have to render it as an html page and then read it in
# the same way you do with networkx visualizations.

	plt.style.use('seaborn-whitegrid')
#upload main data for blended rank and blended rank change viz

	dfbr = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/TotalOrganicKeywords-Jan2021vsJan2022.csv")
	dff = filterterm(dfbr, scatterterm, scattersearch)
	termresults = "yes"
	if dff.isnull().values.any():
		message.text("No results for your term. Check the data below to find a valid keyword.")
		st.dataframe(dfbr)
		termresults = "no"
	elif scatterterm != 'no' or termresults !="no":
		if scattertype == "Blended Rank":
			fig = px.scatter(dff, x="Blended Rank", y="Search Volume",
				text="CustomerSearch",
				log_x=True,
				size="Blended Rank",
				color="Blended Rank",
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
				log_x=False,
				error_x_minus="Blended Rank Change",
				size="Blended Rank",
				color="Blended Rank",
				size_max=25)

				#fig.update_traces(textposition='top center')
			fig.update_traces(mode="markers")
			fig.update_layout(
				height=800,
				title_text='Blended Rank Change and Search Volume'
			)
		elif scattertype == "Combined Keyword":
			dfck = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/combinedKeywords.csv")
			dff = filterterm(dfck, scatterterm, 'volume')

			fig = px.bar(dff, x="Keyword", y=dff['Volume'], color="Portal", title="Combined Keywords")
			#Other variations of representation
			#fig = px.bar(dff, x="Keyword", y=dff['Volume'].astype(int), color=dff['Volume'].astype(int), title="Combined Keywords")
			#fig = px.bar(df1, x=df1.time, y=df2.market, color=df1.sales)


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
def noresults(df):
	st.dataframe(df)
	return df
	#fig2.write_html("scatter.html")
