import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import os
import base64
from .config import db_username, db_password, db_host, db_port, db_name, default_schema


def table_relationships():
    st.title("Table Relationships Viewer")

    # Sidebar controls
    st.sidebar.header("Controls")
    graph_height = st.sidebar.slider("Graph Height", min_value=600, max_value=1200, value=800, step=100)
    export_with_background = st.sidebar.checkbox("Export with background", value=False)
    background_color = st.sidebar.color_picker("Choose background color", "#222222")

    # Physics controls
    st.sidebar.subheader("Graph Physics")
    gravitational_constant = st.sidebar.slider("Gravitational Constant", -100, 0, -26)
    central_gravity = st.sidebar.slider("Central Gravity", 0.0, 1.0, 0.005, 0.001)
    spring_length = st.sidebar.slider("Spring Length", 10, 500, 230)
    spring_constant = st.sidebar.slider("Spring Constant", 0.0, 1.0, 0.18, 0.01)

    
    staging_db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    conn = st.connection(name="postgresql_staging", type="sql", url=staging_db_url)

    # Get all schemas
    schemas_query = "SELECT schema_name FROM information_schema.schemata;"
    schemas = conn.query(schemas_query)['schema_name'].tolist()

    # Schema selection
    selected_schema = st.selectbox("Select Schema", schemas, index=schemas.index('public') if 'public' in schemas else 0)

    # Fetch table relationships
    relationships_query = f"""
    SELECT
        tc.table_name AS table_name,
        kcu.column_name AS column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = '{selected_schema}';
    """
    relationships = conn.query(relationships_query)

    if not relationships.empty:
        # Create a graph
        G = nx.Graph()

        # Add nodes and edges
        for _, row in relationships.iterrows():
            table1 = row['table_name']
            col1 = row['column_name']
            table2 = row['foreign_table_name']
            col2 = row['foreign_column_name']

            G.add_node(f"{table1}.{col1}", title=f"{table1}.{col1}", group=table1)
            G.add_node(f"{table2}.{col2}", title=f"{table2}.{col2}", group=table2)
            G.add_edge(f"{table1}.{col1}", f"{table2}.{col2}")

        # Create a PyVis network
        net = Network(height=f"{graph_height}px", width="100%", bgcolor="#222222", font_color="white")
        
        # Add nodes
        for node in G.nodes(data=True):
            net.add_node(node[0], title=node[1]['title'], group=node[1]['group'])
        
        # Add edges
        for edge in G.edges():
            net.add_edge(edge[0], edge[1])

        # Set options
        net.set_options(f"""
        var options = {{
          "nodes": {{
            "font": {{
              "size": 14
            }}
          }},
          "edges": {{
            "color": {{
              "inherit": true
            }},
            "smooth": false
          }},
          "physics": {{
            "forceAtlas2Based": {{
              "gravitationalConstant": {gravitational_constant},
              "centralGravity": {central_gravity},
              "springLength": {spring_length},
              "springConstant": {spring_constant}
            }},
            "maxVelocity": 146,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {{
              "enabled": true,
              "iterations": 1000,
              "updateInterval": 25
            }}
          }}
        }}
        """)

        # Save and read graph as HTML file
        net.save_graph("pyvis_graph.html")
        with open("pyvis_graph.html", 'r', encoding='utf-8') as f:
            html_string = f.read()
        
        # Add JavaScript for image export
        html_string += f"""
        <script>
        function exportImage() {{
            const canvas = document.querySelector('canvas');
            const context = canvas.getContext('2d');
            const exportWithBackground = {str(export_with_background).lower()};
            const backgroundColor = "{background_color}";
            
            if (exportWithBackground) {{
                // Create a new canvas with the same dimensions
                const exportCanvas = document.createElement('canvas');
                exportCanvas.width = canvas.width;
                exportCanvas.height = canvas.height;
                const exportContext = exportCanvas.getContext('2d');
                
                // Fill the background
                exportContext.fillStyle = backgroundColor;
                exportContext.fillRect(0, 0, canvas.width, canvas.height);
                
                // Draw the original canvas on top
                exportContext.drawImage(canvas, 0, 0);
                
                // Use the new canvas for the image data
                var image = exportCanvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
            }} else {{
                var image = canvas.toDataURL("image/png").replace("image/png", "image/octet-stream");
            }}
            
            const link = document.createElement('a');
            link.download = 'graph.png';
            link.href = image;
            link.click();
        }}
        </script>
        <button onclick="exportImage()">Export as Image</button>
        """
        
        # Display the graph
        st.components.v1.html(html_string, height=graph_height + 50)  # Added extra height for the button

    else:
        st.write("No relationships found in the selected schema.")

if __name__ == "__main__":
    table_relationships()