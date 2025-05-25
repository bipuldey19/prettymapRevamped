import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import tempfile
import os
import geopandas as gpd
from shapely.geometry import shape
from utils import (
    get_available_themes,
    get_default_style,
    get_default_landcover,
    generate_map,
    save_map_data
)

# Set page config with reduced width
st.set_page_config(
    page_title="Prettymapp Generator",
    page_icon="🗺️",
    layout="centered"
)

# Create a container with max width
with st.container():
    # Title and description
    st.title("🗺️ Prettymapp Generator")
    st.markdown("Create beautiful maps from OpenStreetMap data. You can either upload your own boundary file or draw an area on the map.")

    # File upload section
    st.markdown("### Step 1: Upload Boundary File (Optional)")
    st.markdown("You can upload a KML or Shapefile to define your map area. If you don't have a file, you can draw on the map in the next step.")
    uploaded_file = st.file_uploader(
        "Upload KML or Shapefile",
        type=['kml', 'shp', 'zip'],
        help="Upload a KML file or a zipped Shapefile containing your area boundary"
    )

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.kml'):
                gdf = gpd.read_file(uploaded_file, driver='KML')
            else:  # Shapefile
                gdf = gpd.read_file(uploaded_file)
            
            # Convert to GeoJSON
            st.session_state.drawn_polygon = json.loads(gdf.to_json())['features'][0]['geometry']
            st.success("File uploaded successfully! You can now proceed to Step 3.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    # Map section
    st.markdown("### Step 2: Draw on Map")
    st.markdown("Use the drawing tools in the top-left corner to draw a rectangle or circle on the map. This will define the area for your map.")
    
    # Create map with full width
    m = folium.Map(location=[0, 0], zoom_start=2, width='100%')
    
    # Add drawing tools
    folium.plugins.Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': False,
            'rectangle': True,
            'circle': True,
            'circlemarker': False,
            'marker': False,
        }
    ).add_to(m)

    # Display the map and capture drawn features
    drawn_data = st_folium(
        m,
        height=500,
        width='100%',
        returned_objects=["last_active_drawing"]
    )

    # Update session state with drawn polygon
    if drawn_data and drawn_data.get("last_active_drawing"):
        st.session_state.drawn_polygon = drawn_data["last_active_drawing"]

    # Export drawn area button
    if st.session_state.drawn_polygon:
        if st.button("Export Drawn Area", type="secondary"):
            # Convert to GeoJSON and download
            geom = shape(st.session_state.drawn_polygon)
            gdf = gpd.GeoDataFrame(geometry=[geom])
            with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp:
                gdf.to_file(tmp.name, driver='GeoJSON')
                with open(tmp.name, 'rb') as f:
                    st.download_button(
                        "Download Drawn Area",
                        f,
                        file_name="drawn_area.geojson",
                        mime="application/json"
                    )
            os.unlink(tmp.name)

    # Theme selection
    st.markdown("### Step 3: Choose Map Style")
    st.markdown("Select a predefined style for your map. Each style has its own color scheme and visual characteristics.")
    theme = st.selectbox(
        "Select Theme",
        options=get_available_themes(),
        index=0,
        help="Choose a style that best matches your needs"
    )

    # Additional settings in an expander
    st.markdown("### Step 4: Customize Map Settings (Optional)")
    st.markdown("Fine-tune your map's appearance by adjusting these settings. You can leave them as default if you're not sure.")

    with st.expander("Advanced Settings", expanded=False):
        # Style settings
        st.markdown("#### Map Colors and Appearance")
        default_style = get_default_style()
        
        # Create sections for each style category
        for category, settings in default_style.items():
            st.markdown(f"**{category.title()}**")
            for key, value in settings.items():
                if isinstance(value, (int, float)):
                    default_style[category][key] = st.number_input(
                        f"{key}",
                        value=value,
                        key=f"style_{category}_{key}",
                        help=f"Adjust the {key} for {category}"
                    )
                elif isinstance(value, str) and value.startswith('#'):
                    # Color picker for hex colors
                    default_style[category][key] = st.color_picker(
                        f"{key}",
                        value=value,
                        key=f"style_{category}_{key}",
                        help=f"Choose a color for {key} in {category}"
                    )
                elif isinstance(value, str):
                    default_style[category][key] = st.text_input(
                        f"{key}",
                        value=value,
                        key=f"style_{category}_{key}",
                        help=f"Enter {key} for {category}"
                    )
                elif isinstance(value, list):
                    if all(isinstance(x, str) and x.startswith('#') for x in value):
                        # Color picker for lists of hex colors
                        colors = st.multiselect(
                            f"{key}",
                            options=value,
                            default=value,
                            key=f"style_{category}_{key}",
                            help=f"Select colors for {key} in {category}"
                        )
                        default_style[category][key] = colors if colors else value
                    else:
                        default_style[category][key] = st.text_input(
                            f"{key} (comma-separated)",
                            value=",".join(value),
                            key=f"style_{category}_{key}",
                            help=f"Enter values for {key} in {category}, separated by commas"
                        ).split(",")
        
        # Landcover settings
        st.markdown("#### Map Features")
        st.markdown("Choose which features to include in your map (e.g., buildings, roads, water bodies)")
        default_landcover = get_default_landcover()
        
        for category, settings in default_landcover.items():
            st.markdown(f"**{category.title()}**")
            for key, value in settings.items():
                if isinstance(value, bool):
                    default_landcover[category][key] = st.checkbox(
                        f"{key}",
                        value=value,
                        key=f"landcover_{category}_{key}",
                        help=f"Include {key} in the {category} category"
                    )
                elif isinstance(value, list):
                    default_landcover[category][key] = st.multiselect(
                        f"{key}",
                        options=value,
                        default=value,
                        key=f"landcover_{category}_{key}",
                        help=f"Select which {key} to include in {category}"
                    )

    # Generate map button
    st.markdown("### Step 5: Generate Your Map")
    st.markdown("Click the button below to create your map with the selected settings.")
    if st.button("Generate Map", type="primary"):
        if st.session_state.drawn_polygon:
            with st.spinner("Generating your map..."):
                try:
                    fig, df = generate_map(
                        geometry=st.session_state.drawn_polygon,
                        style=theme,
                        custom_settings=default_style,
                        custom_landcover=default_landcover
                    )
                    st.session_state.map_fig = fig
                    st.session_state.map_data = df
                    
                    # Add some space
                    st.markdown("---")
                    
                    # Display the generated map
                    st.markdown("### Your Generated Map")
                    st.pyplot(fig.plot_all())
                    
                    # Download buttons
                    st.markdown("### Download Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        # Save and download the image
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            fig.plot_all().savefig(tmp.name)
                            with open(tmp.name, 'rb') as f:
                                st.download_button(
                                    "Download Map Image",
                                    f,
                                    file_name="pretty_map.png",
                                    mime="image/png"
                                )
                        os.unlink(tmp.name)
                    
                    with col2:
                        # Save and download the data
                        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp:
                            save_map_data(df, tmp.name)
                            with open(tmp.name, 'rb') as f:
                                st.download_button(
                                    "Download Map Data",
                                    f,
                                    file_name="map_data.geojson",
                                    mime="application/json"
                                )
                        os.unlink(tmp.name)
                        
                except Exception as e:
                    st.error(f"Error generating map: {str(e)}")
        else:
            st.warning("Please draw an area on the map or upload a boundary file first.") 