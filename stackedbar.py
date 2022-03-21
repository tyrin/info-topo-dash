import altair as alt
import pandas as pd
import numpy as np
import streamlit as st

data = pd.read_csv("https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv")
source = data.barley()

alt.Chart(source).mark_bar().encode(
    x='variety',
    y='sum(yield)',
    color='site'
)