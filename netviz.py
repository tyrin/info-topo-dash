#run from app.py
from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import os
import sys
import pandas as pd

def convert_df(frame):
	return frame.to_csv().encode('utf-8')

def showresults(frame, file, physics):
	HtmlFile = open("data.html", 'r', encoding='utf-8')
	source_code = HtmlFile.read()
	if physics:
		components.html(source_code, height = 1200,width=900)
	else:
		components.html(source_code, height = 775,width=900)
	st.dataframe(frame)
	csv = convert_df(frame)
	csvname = file + ".csv"
	st.download_button(
	   "Press to Download",
	   csv,
	   csvname,
	   "text/csv",
	   key='download-csv'
	)
def main(ref):
	domain=""
	#--------------------
	#read inputfile
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/data.csv")

#define variables that the customer will input
	sitelist= df['Portal'].unique()
	site = np.sort(sitelist)
	domain=""
	portal=""
	portal = st.sidebar.multiselect(
	'Portal:', site)
	message = st.empty()
	if len(portal) == 0:
		message.text("Select a portal and content domain.")

	if (len(portal) > 0) and (len(domain) == 0):
		message = st.empty()
		#get unique values for content domain
		dfa = df.loc[df['Portal'].isin(portal)]
		dfb = dfa.sort_values(by='Group')
		group = dfb['Group'].unique()
		domain = st.sidebar.multiselect('Content Domain:', group)
		# filter data by portal
		dfc = df.loc[df['Portal'].isin(portal)]
		physics = st.sidebar.checkbox('Add physics interactivity?')
		#frame = st.sidebar.checkbox('Show table data?')
		graphtitle = 'Network graph for ' + ','.join(domain) + ' ' + 'conrefs:'
		st.write(graphtitle)
		#netviz module refrender(relationship, domain, physics)
		message = st.empty()
		refrender(ref, domain, physics)

def refrender(ref, domain, physics):

	# set the network options
	ccx_net = Network(height='750px', width='100%', bgcolor='white', font_color='blue', heading="")

	#read inputfile
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/data.csv")
	#set outputfile
	# filter by domain
	if domain=='all':
		dfff = df.loc[df['Ref'] == ref]

	else:
		dff = df.loc[(df['Group'].isin(domain)) | (df['TargetGroup'].isin(domain))]
		dfff = dff.loc[dff['Ref'] == ref]

	sources = dfff['Source']
	targets = dfff['Target']
	weights = dfff['Weight']
	refs = dfff['Ref']
	groups = dfff['Group']
	colors = dfff['Color']
	labels = dfff['Label']
	tgtgroup = dfff['TargetGroup']
	tgtcolors = dfff['TargetColor']
	tgtlabels = dfff['TargetLabel']

	edge_data = zip(sources, targets, weights, refs, groups, colors, labels, tgtgroup, tgtcolors, tgtlabels)

	for e in edge_data:
		src = e[0]
		tgt = e[1]
		w = e[2]
		rt = e[3]
		grp = e[4]
		clr = e[5]
		lbl = e[6]
		tgtgrp = e[7]
		tgtclr = e[8]
		tgtlbl = e[9]

	# node_id, label, named args
		ccx_net.add_node(src, lbl, title=src, color=clr)
		ccx_net.add_node(tgt, tgtlbl, title=tgt, color=tgtclr)
		ccx_net.add_edge(src, tgt, value=w)

	neighbor_map = ccx_net.get_adj_list()

	# add neighbor data to node hover data
	for node in ccx_net.nodes:
		node['title'] += '<br> Neighbors: <br>' + '<br>'.join(neighbor_map[node['id']])
		node['value'] = len(neighbor_map[node['id']])

	if physics:
		ccx_net.show_buttons(filter_=['physics'])
		ccx_net.show("data.html")
		showresults(dfff, ref, physics)

	else:
		ccx_net.show("data.html")
		showresults(dfff, ref, physics)
	#display(HTML(outputfile))
