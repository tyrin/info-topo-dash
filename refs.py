#run from app.py
from pyvis.network import Network
import numpy as np
import os
import sys
import pandas as pd

def vizrender(ref, domain, physics, search, term):
	ccx_net = Network(height='750px', width='100%', bgcolor='white', font_color='blue')

	# set the network options
	ccx_net.set_options('''
	var options = {
		"configure": {
			"enabled": false
		},
		"edges": {
		"arrows": {
			"to": {
			"enabled": true
			}
		},
		"color": {
			"inherit": true
		},
		"smooth": false
		},
		"interaction": {
		"hideEdgesOnDrag": true
		},
		"physics": {
		"barnesHut": {
			"gravitationalConstant": -80000,
			"springLength": 135,
			"springConstant": 0.001,
			"damping": 0.42,
			"avoidOverlap": 0.75
		},
		"minVelocity": 0.75
		}
	}
	''')

	#read inputfile
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/data.csv")
	#set outputfile
	# filter by relationship and domain
	if ref == 'all' and 'all' in domain:
		dff = df

	elif	ref=='all':
		dff = df.loc[df['Group'].isin(domain)]

	elif domain=='all':
		dff = df.loc[df['Ref'] == ref]

	else:
		dff = df.loc[(df['Group'].isin(domain)) & (df['Ref'] == ref)]
# keyword filtering
	if term == 'no':
		dfff = dff

	elif	search=='label':
		dfff = dff.loc[(df['Label'].str.contains(term)) | (df['TargetLabel'].str.contains(term))]

	else:
		dfff = dff.loc[(df['Source'].str.contains(term)) | (df['Target'].str.contains(term))]

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
		ccx_net.show("data.html")
	else:
		ccx_net.show("data.html")
	#display(HTML(outputfile))
