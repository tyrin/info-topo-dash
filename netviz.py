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

def showresults(frame, file):
	HtmlFile = open("data.html", 'r', encoding='utf-8')
	source_code = HtmlFile.read()
	components.html(source_code, height = 1200,width=900)
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
	if ref=='choose':
		ref = st.sidebar.radio(
			"Reference Type:",
			('conref', 'xref', 'all'))
	domains=""
	domains = st.sidebar.multiselect(
	'Content Domain:',
	['all', 'ajax', 'android_native_development', 'android', 'apex', 'api', 'api_action', 'api_analytics', 'api_asynch', 'api_bulk_v2', 'api_c360a', 'api_cti', 'api_datadotcom_dev_guide', 'api_datadotcom_match', 'api_datadotcom_search', 'api_df', 'api_dj', 'api_gateway', 'api_gpl', 'api_iot', 'api_meta', 'api_rest', 'api_rest_encryption', 'api_streaming', 'api_tooling', 'api_ui', 'aura', 'b2b_comm_lex', 'b2b_commerce', 'canvas', 'change_data_capture', 'chat', 'chat_rest', 'chatter_connect', 'cms', 'communities_dev', 'connectapi', 'daas', 'data', 'developer', 'eclipse', 'exp_cloud_lwr', 'field_service', 'forcecom', 'fsc_api', 'healthcare_api', 'industries', 'integration_patterns', 'ios', 'ios_native_development', 'knowledge', 'langCon', 'limits', 'loyalty', 'manufacturing_api', 'maps', 'methods', 'mobile_sdk', 'ns_healthcloudext', 'ns_LoyaltyManagement', 'objects', 'omnichannel', 'one_c', 'order_management', 'pages', 'platform_connect', 'platform_events', 'psc_api', 'rebates_api', 'reference', 'resource', 'resources', 'restriction_rules', 'salesforce_scheduler', 'salesforce1', 'scoping_rules', 'secure_coding', 'service_sdk', 'sfdx_cli', 'sfdx_dev', 'sfdx_setup', 'soql_sosl', 'source_files', 'sustainability', 'voice', 'voice_pt', 'vpm', 'workdotcom']
  )
	physics = st.sidebar.checkbox('Add physics interactivity?')
	if len(domains) == 0:
		st.write('Select one or more content domains in the sidebar to analyze.')
	else:
		graphtitle = 'Network graph for ' + ','.join(domains) + ' ' + 'conrefs:'
		st.write(graphtitle)
		#netviz module refrender(relationship, domain, physics)
		refrender(ref, domains, physics)



def refrender(ref, domain, physics):
    # set the network options
    ccx_net = Network(height='750px', width='100%', bgcolor='white', font_color='blue', heading="")

    #read inputfile
    df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data.csv")
    #set outputfile
    # filter by domain
    if domain=='all':
        dfff = df.loc[df['Ref'] == ref]

    else:
        dfff = df.loc[(df['Group'].isin(domain)) & (df['Ref'] == ref)]

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
        showresults(dfff, ref)

    else:
        ccx_net.show("data.html")
        showresults(dfff, ref)
    #display(HTML(outputfile))

def vizrender(ref, domain, physics, search, term):
    # set the network options
    ccx_net = Network(height='750px', width='100%', bgcolor='white', font_color='blue', heading="")

    #read inputfile
    df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data.csv")
    #set outputfile
    # filter by relationship and domain
    if ref == 'all' and 'all' in domain:
        dff = df

    elif  ref=='all':
        dff = df.loc[df['Group'].isin(domain)]

    elif domain=='all':
        dff = df.loc[df['Ref'] == ref]

    else:
        dff = df.loc[(df['Group'].isin(domain)) & (df['Ref'] == ref)]
# keyword filtering
    if term == 'no':
        dfff = dff

    elif  search=='label':
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
