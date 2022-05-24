import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import plotly.figure_factory as ff
import plotly.express as px

def main():
	#st.write(px.colors.sequential.Aggrnyl)
	#st.write(px.colors.carto.swatches())
	#st.write(px.colors.cmocean.swatches())
	#st.write(px.colors.colorbrewer.swatches())
	st.write(px.colors.cyclical.swatches())
	st.write(px.colors.diverging.swatches())
	st.write(px.colors.qualitative.swatches())
	st.write(px.colors.sequential.swatches())

