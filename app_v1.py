import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import relationships
#Network(notebook=True)
st.title('Content Domain Relationships for Developer Doc')
# make Network show itself with repr_html

#def net_repr_html(self):
#  nodes, edges, height, width, options = self.get_network_data()
#  html = self.template.render(height=height, width=width, nodes=nodes, edges=edges, options=options)
#  return html

#Network._repr_html_ = net_repr_html
st.sidebar.title('Choose the visualization:')
option=st.sidebar.selectbox('select a relationship',('All','Conrefs', 'Xrefs'))
#physics=st.sidebar.checkbox('add physics interactivity?')
#relationships.simple_func(physics)

if option=='All':
  HtmlFile = open("All.html", 'r', encoding='utf-8')
  source_code = HtmlFile.read()
  components.html(source_code, height = 900,width=900)


#relationships.relationships_func(physics)

if option=='Conrefs':
  HtmlFile = open("Conrefs.html", 'r', encoding='utf-8')
  source_code = HtmlFile.read()
  components.html(source_code, height = 1200,width=1000)



#relationships.karate_func(physics)

if option=='Xrefs':
  HtmlFile = open("Xrefs.html", 'r', encoding='utf-8')
  source_code = HtmlFile.read()
  components.html(source_code, height = 1200,width=1000)
