import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import tempfile
import os
from utils import (
    get_available_themes,
    get_default_style,
    get_default_landcover,
    generate_map,
    save_map_data
)

st.set_page_config(
    page_title="Prettymapp Generator",
    page_icon="🗺️",
    layout="wide"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🗺️ Prettymapp Generator")
st.markdown("Create beautiful maps from OpenStreetMap data using an interactive map interface.")

# Initialize session state
if 'drawn_polygon' not in st.session_state:
    st.session_state.drawn_polygon = None
if 'map_fig' not in st.session_state:
    st.session_state.map_fig = None
if 'map_data' not in st.session_state:
    st.session_state.map_data = None

# Main container for the app
main_container = st.container()

with main_container:
    # Create three columns for the layout
    map_col, settings_col, action_col = st.columns([3, 2, 1], gap="medium")

    with map_col:
        st.subheader("Draw Area")
        # Create a map centered at a default location
        m = folium.Map(location=[0, 0], zoom_start=2)
        
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
            returned_objects=["last_active_drawing"]
        )
        
        # Update session state with drawn polygon
        if drawn_data and drawn_data.get("last_active_drawing"):
            st.session_state.drawn_polygon = drawn_data["last_active_drawing"]

    with settings_col:
        st.subheader("Theme")
        # Theme selection
        theme = st.selectbox(
            "Select Theme",
            options=get_available_themes(),
            index=0,
            label_visibility="collapsed"
        )

    with action_col:
        st.subheader("Generate")
        # Generate map button
        if st.button("Generate Map", use_container_width=True):
            if st.session_state.drawn_polygon:
                with st.spinner("Generating map..."):
                    try:
                        fig, df = generate_map(
                            geometry=st.session_state.drawn_polygon,
                            style=theme,
                            custom_settings=default_style,
                            custom_landcover=default_landcover
                        )
                        st.session_state.map_fig = fig
                        st.session_state.map_data = df
                        
                        # Display the generated map
                        st.pyplot(fig.plot_all())
                        
                        # Download buttons in a container
                        with st.container():
                            download_col1, download_col2 = st.columns(2, gap="small")
                            with download_col1:
                                # Save and download the image
                                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                                    fig.plot_all().savefig(tmp.name)
                                    with open(tmp.name, 'rb') as f:
                                        st.download_button(
                                            "Download Map Image",
                                            f,
                                            file_name="pretty_map.png",
                                            mime="image/png",
                                            use_container_width=True
                                        )
                                os.unlink(tmp.name)
                            
                            with download_col2:
                                # Save and download the data
                                with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp:
                                    save_map_data(df, tmp.name)
                                    with open(tmp.name, 'rb') as f:
                                        st.download_button(
                                            "Download Map Data",
                                            f,
                                            file_name="map_data.geojson",
                                            mime="application/json",
                                            use_container_width=True
                                        )
                                os.unlink(tmp.name)
                                
                    except Exception as e:
                        st.error(f"Error generating map: {str(e)}")
            else:
                st.warning("Please draw an area on the map first.")

# Settings section in a container
settings_container = st.container()

with settings_container:
    # Create tabs for different settings
    style_tab, landcover_tab = st.tabs(["Style Settings", "Landcover Settings"])
    
    with style_tab:
        default_style = get_default_style()
        # Create columns for style settings
        style_cols = st.columns(2, gap="medium")
        for i, (category, settings) in enumerate(default_style.items()):
            with style_cols[i % 2]:
                with st.container():
                    st.markdown(f"#### {category.title()}")
                    for key, value in settings.items():
                        if isinstance(value, (int, float)):
                            default_style[category][key] = st.number_input(
                                f"{key}",
                                value=value,
                                key=f"style_{category}_{key}"
                            )
                        elif isinstance(value, str):
                            default_style[category][key] = st.text_input(
                                f"{key}",
                                value=value,
                                key=f"style_{category}_{key}"
                            )
                        elif isinstance(value, list):
                            default_style[category][key] = st.text_input(
                                f"{key} (comma-separated)",
                                value=",".join(value),
                                key=f"style_{category}_{key}"
                            ).split(",")
    
    with landcover_tab:
        default_landcover = get_default_landcover()
        # Create columns for landcover settings
        landcover_cols = st.columns(2, gap="medium")
        for i, (category, settings) in enumerate(default_landcover.items()):
            with landcover_cols[i % 2]:
                with st.container():
                    st.markdown(f"#### {category.title()}")
                    for key, value in settings.items():
                        if isinstance(value, bool):
                            default_landcover[category][key] = st.checkbox(
                                f"{key}",
                                value=value,
                                key=f"landcover_{category}_{key}"
                            )
                        elif isinstance(value, list):
                            default_landcover[category][key] = st.multiselect(
                                f"{key}",
                                options=value,
                                default=value,
                                key=f"landcover_{category}_{key}"
                            ) 