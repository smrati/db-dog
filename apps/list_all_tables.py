import os
import streamlit as st
import time
import pandas as pd
import math
from .config import db_username, db_password, db_host, db_port, db_name, default_schema



def list_all_tables():
    st.title("List All Tables")
    st.write("This is the list of all tables.")

    # Construct the database URL
    staging_db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = st.connection(name=f"postgresql_staging", type="sql", url=staging_db_url)

    # Query to get all available schemas
    schema_query = "SELECT schema_name FROM information_schema.schemata;"
    schemas_df = conn.query(schema_query)
    schema_list = schemas_df['schema_name'].tolist()

    # Add dropdown for schema selection
    selected_schema = st.selectbox("Select schema:", schema_list, index=schema_list.index(default_schema) if default_schema in schema_list else 0)

    # Query to get tables from the selected schema and their foreign key relationships
    table_query = f"""
    SELECT 
        t.table_name,
        string_agg(fk.table_name, ', ') as referencing_tables
    FROM 
        information_schema.tables t
    LEFT JOIN (
        SELECT
            ccu.table_name AS table_name,
            tc.table_name AS referencing_table
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = '{selected_schema}'
    ) fk ON t.table_name = fk.referencing_table
    WHERE 
        t.table_schema = '{selected_schema}'
    GROUP BY 
        t.table_name;
    """
    result_df = conn.query(table_query)
    
    # Convert to pandas DataFrame and set column names
    result_df = pd.DataFrame(result_df, columns=['table_name', 'referencing_tables'])
    
    # Function to show table preview
    def show_table_preview(table_name, selected_schema):
        # First, check if the table exists in the selected schema
        check_table_query = f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = '{selected_schema}' 
            AND table_name = '{table_name}'
        );
        """
        table_exists = conn.query(check_table_query).iloc[0, 0]

        if table_exists:
            preview_query = f"SELECT * FROM {selected_schema}.{table_name} LIMIT 5;"
            preview_df = conn.query(preview_query)
            st.write(f"Preview of {table_name}:")
            st.dataframe(preview_df)
        else:
            st.write(f"Table '{table_name}' does not exist in schema '{selected_schema}' or cannot be previewed.")

    # Initialize session state for preview visibility
    if 'visible_preview' not in st.session_state:
        st.session_state.visible_preview = None

    # Render the buttons in a grid
    num_buttons = len(result_df)
    buttons_per_row = 5  # Adjust this number to change the number of buttons per row
    num_rows = math.ceil(num_buttons / buttons_per_row)

    for i in range(num_rows):
        cols = st.columns(buttons_per_row)
        for j in range(buttons_per_row):
            index = i * buttons_per_row + j
            if index < num_buttons:
                table_name = result_df.iloc[index]['table_name']
                if cols[j].button(table_name, key=f"btn_{index}"):
                    if st.session_state.visible_preview == table_name:
                        st.session_state.visible_preview = None
                    else:
                        st.session_state.visible_preview = table_name

    # Show preview for the selected table
    if st.session_state.visible_preview:
        show_table_preview(st.session_state.visible_preview, selected_schema)

    # Render the dataframe with both columns
    st.dataframe(
        result_df,
        height=500,
        use_container_width=True,
        hide_index=True,
        column_config={
            "table_name": st.column_config.TextColumn(
                "Table Name",
                width="medium"
            ),
            "referencing_tables": st.column_config.TextColumn(
                "Tables with Foreign Keys to This Table",
                width="large"
            )
        }
    )