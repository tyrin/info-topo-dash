#run from app.py
from pyvis.network import Network
import numpy as np
import os
import sys
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
def main():
#read inputfile
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/data.csv")

#define variables that the customer will input
	site= df['Portal'].unique()
	domain=""
	portal=""
	portal = st.sidebar.multiselect(
	'Portal:', site)
	message = st.empty()
	if len(portal) == 0:
		message.text("Select a portal and/or content domain to filter results")

	if (len(portal) > 0) and (len(domain) == 0):
		message.text("By default, shows all references for all reference types. Filter for faster rendering of the graph.")
		#get unique values for content domain
		dfa = df.loc[df['Portal'].isin(portal)]
		dfb = dfa.sort_values(by='Group')
		group = dfb['Group'].unique()
		domain = st.sidebar.multiselect('Content Domain:', group)
		# filter data by portal
		dfc = df.loc[df['Portal'].isin(portal)]
		#show other filters
		ref = st.sidebar.radio(
			"Reference Type:",
			('all', 'conref', 'xref'))

		search = st.sidebar.radio(
			"Keyword search for:",
			('labels', 'nodes'))
		searchterm = st.sidebar.text_input('Enter a keyword', value="", max_chars=25)

		physics = st.sidebar.checkbox('Add physics interactivity?')
		frame = st.sidebar.checkbox('Show raw data?')

		if len(searchterm) == 0:
			term = 'no'
		else:
			term = searchterm
		graphtitle = 'Complex network graph of ' + ref + " references for "+ ' all domain(s) with ' + term + " keywords"
		complexviz(ref, "all", physics, search, term, dfa, frame)
	if (len(portal) > 0) and (len(domain) > 0):
		dfc = df.loc[(df['Portal'].isin(portal)) & (df['Group'].isin(domain))]
		graphtitle = 'Complex network graph of ' + ref + " references for "+ ','.join(domain) + ' domain(s) with ' + term + " keywords"
		st.write(graphtitle)
		#complexviz(title, relationship, domain, physics, search, term)
		complexviz(ref, domain, physics, search, term, dfc, frame)

def complexviz(ref, domains, physics, search, term, dfc, frame):
    message = st.empty()
    # set the network options
    ccx_net = Network(height='750px', width='750', bgcolor='white', font_color='blue', heading="")

    # filter by relationship and domains
    if ref == 'all' and 'all' in domains:
        dff = dfc

    elif  ref=='all':
        dff = dfc.loc[dfc['Group'].isin(domains)]

    elif domains=='all':
        dff = dfc.loc[dfc['Ref'] == ref]

    else:
        dfd = dfc.loc[(dfc['Group'].isin(domain)) | (dfc['TargetGroup'].isin(domain))]
        dff = dfd.loc[dfc['Ref'] == ref]
# keyword filtering
    if term == 'no':
        dfff = dff

    elif  search=='label':
        dfff = dff.loc[(dff['Label'].str.contains(term)) | (dff['TargetLabel'].str.contains(term))]

    else:
        dfff = dff.loc[(dff['Source'].str.contains(term)) | (dff['Target'].str.contains(term))]

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
        node['title'] += ' Neighbors:<br>' + '<br>'.join(neighbor_map[node['id']])
        node['value'] = len(neighbor_map[node['id']])
    if physics:
        ccx_net.show_buttons(filter_=['physics'])
        ccx_net.show("complexdata.html")
    else:
        message = st.empty()
        ccx_net.show("complexdata.html")
    HtmlFile = open("complexdata.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    if physics == 'True':
        components.html(source_code, height = 1200,width=900)
    else:
        components.html(source_code, height = 775,width=900)
    if frame:
        st.dataframe(dfc)

