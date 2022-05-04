#run from app.py
from pyvis.network import Network
import numpy as np
import os
import sys
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
def evaluate(frame, portal, domain, ref, search, searchterm, physics, showdf):
# if portal list is empty it's considered false, then filter by value
# frame passed is already filtered by portal, since that was necessary to get the domain list for the sidebar
	if not portal:
		portaldesc = "All"
	else:
		portaldesc = portal
# domain filter to dfc
	if domain:
		dfc = frame.loc[(frame['Group'].isin(domain)) | (frame['TargetGroup'].isin(domain))]

	else:
		dfc = frame
# reference filter to dfd
	if ref == 'all':
		dfd = dfc
	else:
		dfd = dfc.loc[dfc['Ref'] == ref]
		#st.write("DFD")
		#st.dataframe(dfd)
# keyword filter to frame
	if len(searchterm) == 0:
		term = 'no'
		frame = dfd
	else:
		term = searchterm
		if  search=='label':
			frame= dfd.loc[(dfd['Label'].str.contains(term)) | (dfd['TargetLabel'].str.contains(term))]
		else:
			frame = dfd.loc[(dfd['Source'].str.contains(term)) | (dfd['Target'].str.contains(term))]
			#st.write("FRAME")
			#st.dataframe(frame)
# render results
	ccx_net = Network(height='750px', width='100%', bgcolor='white', font_color='blue', heading="")

	sources = frame['Source']
	targets = frame['Target']
	weights = frame['Weight']
	refs = frame['Ref']
	groups = frame['Group']
	colors = frame['Color']
	labels = frame['Label']
	tgtgroup = frame['TargetGroup']
	tgtcolors = frame['TargetColor']
	tgtlabels = frame['TargetLabel']

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
		node['title'] += ' Neighbors:<br>' + '<br>'.join(neighbor_map[node['id']])
		node['value'] = len(neighbor_map[node['id']])
	if physics:
		ccx_net.show_buttons(filter_=['physics'])
		ccx_net.show("complexdata.html")
	else:
		#message = st.empty()
		ccx_net.show("complexdata.html")


	HtmlFile = open("complexdata.html", 'r', encoding='utf-8')
	source_code = HtmlFile.read()
	if physics:
		components.html(source_code, height = 1200,width = 900)

	else:
		components.html(source_code, height = 775,width = 900)
	if showdf:
		st.dataframe(frame)
		csv = convert_df(frame)
		csvname = "complex" + ref + ".csv"
		st.download_button(
		   "Press to Download",
		   csv,
		   csvname,
		   "text/csv",
		   key='download-csv'
		)

def main():
#read inputfile
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/data.csv")
	message = st.empty()
# portal input
	site= df['Portal'].unique()
	domain="all"
	portal="all"
	portal = st.sidebar.multiselect(
	'Portal:', site)
# if portal is set, filter domain values by portal
	if len(portal) > 0:
	#if 'all' not in portal:
		dfa = df.loc[df['Portal'].isin(portal)]

	else:
		#get unique values for content domain
		dfa = df
# domain input with unique, sorted list of domain
	dfb = dfa.sort_values(by='Group')
	group = dfb['Group'].unique()
	domain = st.sidebar.multiselect('Content Domain:', group)
# reference type input
	ref = st.sidebar.radio(
		"Reference Type:",
		('all', 'conref', 'xref'))
# search type input
	search = st.sidebar.radio(
		"Keyword search for:",
		('labels', 'nodes'))
	searchterm = st.sidebar.text_input('Enter a keyword', value="", max_chars=25)

	physics = st.sidebar.checkbox('Add physics interactivity?')
	showdf = st.sidebar.checkbox('Show table data?')
	frame = dfa

	if st.sidebar.button('Render'):
		#message.text("It may take some time for the graph to render.")
		evaluate(frame, portal, domain, ref, search, searchterm, physics, showdf)
	else:
		st.markdown('Select filters and click **Render** in the sidebar to see your visualization. ')
	st.write()