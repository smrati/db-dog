import streamlit as st
import pandas as pd
import os
from .config import db_username, db_password, db_host, db_port, db_name, default_schema

def table_viewer():
    st.title("Table Viewer")

    # Sidebar
    st.sidebar.header("Controls")

    
    staging_db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = st.connection(name="postgresql_staging", type="sql", url=staging_db_url)

    # Get all schemas
    schemas_query = "SELECT schema_name FROM information_schema.schemata;"
    schemas = conn.query(schemas_query)['schema_name'].tolist()

    # Schema selection (in sidebar)
    selected_schema = st.sidebar.selectbox("Select Schema", schemas, index=schemas.index('public') if 'public' in schemas else 0)

    # Get tables for selected schema
    tables_query = f"""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = '{selected_schema}' AND table_type = 'BASE TABLE';
    """
    tables = conn.query(tables_query)['table_name'].tolist()

    # Table selection (in sidebar)
    selected_table = st.sidebar.selectbox("Select Table", tables)

    # Number of rows slider
    n_rows = st.sidebar.slider("Number of rows to display", 1, 100, 10)

    if selected_table:
        # Display table info
        st.header("Table Information")
        info_query = f"""
        SELECT 
            column_name, 
            data_type, 
            is_nullable
        FROM 
            information_schema.columns 
        WHERE 
            table_schema = '{selected_schema}' 
            AND table_name = '{selected_table}'
        ORDER BY ordinal_position;
        """
        info = conn.query(info_query)
        st.dataframe(info, use_container_width=True)

        # Get columns for selected table
        columns = info['column_name'].tolist()

        # Order by selection
        order_by = st.sidebar.selectbox("Order by", columns)

        # Fetch data
        data_query = f"""
        SELECT * FROM {selected_schema}.{selected_table} 
        ORDER BY {order_by} 
        LIMIT {n_rows};
        """
        data = conn.query(data_query)

        # Display data
        st.header(f"Table Data Preview")
        st.write(f"Displaying first {n_rows} rows from {selected_schema}.{selected_table} ordered by {order_by}:")
        st.dataframe(data, use_container_width=True)

    else:
        st.write("Please select a schema and table from the sidebar to view data.")

if __name__ == "__main__":
    table_viewer()