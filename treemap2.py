import numpy as np
import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st
def main():
	df = pd.read_csv("https://raw.githubusercontent.com/tyrin/info-topo-dash/master/data/data.csv")

	figx = px.treemap(df[df['Ref'] == "xref"], path=[px.Constant("all"), 'Group', 'Label'],
		values='Weight',
		color='Group',
		color_discrete_sequence=px.colors.sequential.RdBu

		)
	figx.update_layout(margin = dict(t=50, l=25, r=25, b=25))

#to see possible color swatches for plotly
#figz = px.colors.qualitative.swatches()
#st.plotly_chart(figz)

#create conref graph
	figc = px.treemap(df[df['Ref'] == "conref"], path=[px.Constant("all"), 'Group', 'Label'],
	values='Weight',
	color='Group',
	color_discrete_sequence=px.colors.sequential.RdBu
	)
	figc.update_layout(margin = dict(t=50, l=25, r=25, b=25))
	#fig.show()

	st.caption("Conref Treemap")
	st.plotly_chart(figc)

	st.caption("Xref Treemap")
	st.plotly_chart(figx)
	st.dataframe(df[df['Ref'] == "xref"])