import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import refs
st.header("CCX Data Visualization")
st.subheader("Content Dependencies")
#st.write("Examine relationships between different books and clouds.")
#st.title('Content Domain Relationships for Developer Doc')

st.sidebar.title('Choose the visualization:')
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
  graphtitle = 'Network graph for ' + ','.join(domains) + ' ' + ref + 's and ' + term + ' keyword(s)'
  st.write(graphtitle)
  #vizrender(title, relationship, domain, physics, search, term)
  refs.vizrender(ref, domains, physics, search, term)
  HtmlFile = open("data.html", 'r', encoding='utf-8')
  source_code = HtmlFile.read()
  components.html(source_code, height = 1200,width=900)

#	st.write(title, ref, domains, physics)