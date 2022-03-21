# libraries
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import streamlit as st

def main():
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/freshdata.csv")
	site= df['Portal'].unique()
#define variables that the customer will input
	domain=""
	portal=""
	portal = st.sidebar.multiselect(
	'Portal:', site)
	message = st.empty()
	if len(portal) == 0:
		message.text("Select a portal")

	if (len(portal) > 0) and (len(domain) == 0):

		message.text("Select a domain")
		#df[df['country'] == country]
		dff = df.loc[df['Portal'].isin(portal)]
		group = dff['Group'].unique()
		domain = st.sidebar.multiselect('Content Domain:', group)
	if (len(portal) > 0) and (len(domain) > 0):
		message.text("Portal and domain length")
		dfff = df.loc[(df['Portal'].isin(portal)) & (df['Group'].isin(domain))]
		st.dataframe(dfff)
		#next line converts the dates from a pandas object to datetime
		#then uses to_numpty to convert a column into the array needed by the heatmap
		z = pd.to_datetime(dfff['Date'].to_numpy())
		#shows the array
		st.write(z)
		#checks the object type
		st.write(type(z))
		#checks the data type
		st.write(z.dtype)

	#fig = px.imshow(z, text_auto=True)
	#fig.write_html("heat.html")
	#HtmlFile = open("heat.html", 'r', encoding='utf-8')
	#source_code = HtmlFile.read()
	#components.html(source_code, height = 1200,width=900)