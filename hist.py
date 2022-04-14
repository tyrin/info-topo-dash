#plotly distribution plot
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import plotly.figure_factory as ff
import numpy as np
import pandas as pd

def main():
# Add histogram data
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/freshdata.csv")

#define variables that the customer will input
	site= df['Portal'].unique()
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
		dfs = dff.sort_values(by='Group')
		group = dfs['Group'].unique()
		domain = st.sidebar.multiselect('Content Domain:', group)
		dfff = df.loc[df['Portal'].isin(portal)]
		fd = dfff.filter(items=['Date', 'Node'])
		#fd['Date'] = fd['Date'].astype('datetime64[ns]')
		fd['Date'] = fd['Date'].astype('datetime64')
	if (len(portal) > 0) and (len(domain) > 0):
		#message.text("Filter by date")
		dfff = df.loc[(df['Portal'].isin(portal)) & (df['Group'].isin(domain))]
		fd = dfff.filter(items=['Date', 'Node'])
		fd['Date'] = fd['Date'].astype('datetime64')
#Using the below makes causes an error in the streamlit dataframe call, so I have to use the above.
#fd['Date']= pd.to_datetime(df['Date'])

		fig, ax = plt.subplots()
		fd["Date"].astype(np.int64).plot.hist(ax=ax)
		#Creating side bar so it reflect current data
		#min_value = fd.index.min()
		#start_time = st.sidebar.slider(
     	#	"When do you start?",
     	#	value=fd.index.min(),
     	#	format="MM/DD/YY - hh:mm")
		#st.sidebar.write("Start time:", fd.index.min())

		labels = ax.get_xticks().tolist()
		labels = pd.to_datetime(labels)
		ax.set_xticklabels(labels, rotation=90)

		st.pyplot(fig, use_container_width=True)
		st.dataframe(fd)
	@st.cache
	def convert_df(fd):
	   return dff.to_csv().encode('utf-8')
	if len(portal) != 0:
		csv = convert_df(fd)

		st.download_button(
		   "Press to Download",
		   csv,
		   "freshness.csv",
		   "text/csv",
		   key='download-csv'
		)

#---------
# Data type conversions
# my data is datetime64[ns, tzlocal()]
#df['created_at'] = df['created_at'].astype('datetime64[ns]')
#df['user_type'] = df['user_type'].astype('category')
#
## Show new data types
#df.dtypes


#--------
