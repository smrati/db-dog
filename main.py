import streamlit as st
from apps.list_all_tables import list_all_tables
from apps.analyze_table import table_viewer
from apps.table_relationships import table_relationships

st.set_page_config(layout="wide", page_title="DB-dog")
page_list = []

page_list += ["List All Tables", "Analyze Table", "Table Relationships"]

page = st.sidebar.selectbox("Select a page", page_list)

if page == "List All Tables":
    list_all_tables()
elif page == "Analyze Table":
    table_viewer()
elif page == "Table Relationships":
    table_relationships()

