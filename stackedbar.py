import streamlit as st
import plotly.figure_factory as ff
import numpy as np
import pandas as pd
import plotly.express as px
#in this one I'm letting people see all of the items for a portal. So they pic that, the data is filtered
#and then you get a chart with all of the items
def comparebar():
	# Add histogram data
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/freshdata.csv")

	#define variables that the customer will input
	portal=""
	sdf=df.sort_values(by='Portal')
	site= sdf['Portal'].unique()

	portal = st.sidebar.multiselect(
	'Portal:', site)
	message = st.empty()
	if len(portal) == 0:
		message.text("Select a portal")
	#filer the data by the selected portal


	dff = df.loc[df['Portal'].isin(portal)]
	dfs = dff.sort_values(by='Group')
	#group = dfs['Group'].unique()
	# convert the 'Date' column to datetime format
	dfs['Date']= pd.to_datetime(df['Date'])

	# Check the format of 'Date' column
	#dfs.info()

	fig = px.histogram(dfs, x="Date", color="Group")

	## Create distplot with custom bin_size
	#fig = ff.create_distplot(
	#     hist_data, group, bin_size=[.1, .25, .5])
	#
	## Plot!
	st.plotly_chart(fig, use_container_width=True)


