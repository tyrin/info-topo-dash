#run from app.py
from pyvis.network import Network
import numpy as np
import os
import sys
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
def main():
	ref = st.sidebar.radio(
		"Reference Type:",
		('conref', 'xref', 'all'))

	domains = st.sidebar.multiselect(
		'Content Domain:',
		['all', 'ajax', 'android_native_development', 'android', 'apex', 'api', 'api_action', 'api_analytics', 'api_asynch', 'api_bulk_v2', 'api_c360a', 'api_cti', 'api_datadotcom_dev_guide', 'api_datadotcom_match', 'api_datadotcom_search', 'api_df', 'api_dj', 'api_gateway', 'api_gpl', 'api_iot', 'api_meta', 'api_rest', 'api_rest_encryption', 'api_streaming', 'api_tooling', 'api_ui', 'aura', 'b2b_comm_lex', 'b2b_commerce', 'canvas', 'change_data_capture', 'chat', 'chat_rest', 'chatter_connect', 'cms', 'communities_dev', 'connectapi', 'daas', 'data', 'developer', 'eclipse', 'exp_cloud_lwr', 'field_service', 'forcecom', 'fsc_api', 'healthcare_api', 'industries', 'integration_patterns', 'ios', 'ios_native_development', 'knowledge', 'langCon', 'limits', 'loyalty', 'manufacturing_api', 'maps', 'methods', 'mobile_sdk', 'ns_healthcloudext', 'ns_LoyaltyManagement', 'objects', 'omnichannel', 'one_c', 'order_management', 'pages', 'platform_connect', 'platform_events', 'psc_api', 'rebates_api', 'reference', 'resource', 'resources', 'restriction_rules', 'salesforce_scheduler', 'salesforce1', 'scoping_rules', 'secure_coding', 'service_sdk', 'sfdx_cli', 'sfdx_dev', 'sfdx_setup', 'soql_sosl', 'source_files', 'sustainability', 'voice', 'voice_pt', 'vpm', 'workdotcom']
	  )
	search = st.sidebar.radio(
		"Keyword search for:",
		('labels', 'nodes'))
	searchterm = st.sidebar.text_input('Enter a keyword', value="", max_chars=25)

	physics = st.sidebar.checkbox('Add physics interactivity?')

	if len(searchterm) == 0:
		term = 'no'
	else:
		term = searchterm

	#if 'none' in domains:
	if len(domains) == 0:
	  st.write('Select a reference type and domain in the sidebar. Keyword filtering is optional.')
	else:
	  graphtitle = 'Complex network graph of ' + ref + " references for "+ ','.join(domains) + ' domain(s) with ' + term + " keywords"
	  st.write(graphtitle)
  #complexviz(title, relationship, domain, physics, search, term)

	complexviz(ref, domains, physics, search, term)

def complexviz(ref, domain, physics, search, term):
    # set the network options
    ccx_net = Network(height='750px', width='750', bgcolor='white', font_color='blue', heading="")

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
        dfa = df.loc[(df['Group'].isin(domain)) | (df['TargetGroup'].isin(domain))]
        dff = dfa.loc[dfa['Ref'] == ref]
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
        ccx_net.show("complexdata.html")
    else:
        ccx_net.show("complexdata.html")
    HtmlFile = open("complexdata.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height = 1200,width=900)
