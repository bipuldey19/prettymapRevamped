import streamlit as st
import folium
from streamlit_folium import folium_static
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

st.title("🗺️ Prettymapp Generator")
st.markdown("Create beautiful maps from OpenStreetMap data using an interactive map interface.")

# Initialize session state
if 'drawn_polygon' not in st.session_state:
    st.session_state.drawn_polygon = None
if 'map_fig' not in st.session_state:
    st.session_state.map_fig = None
if 'map_data' not in st.session_state:
    st.session_state.map_data = None

# Create two columns for the layout
col1, col2 = st.columns([2, 1])

with col1:
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
    
    # Display the map
    folium_static(m, height=600)
    
    # Get drawn features
    drawn_features = m._children.get('draw', None)
    if drawn_features:
        drawn_data = drawn_features.data
        if drawn_data:
            st.session_state.drawn_polygon = drawn_data[0]

with col2:
    st.subheader("Settings")
    
    # Theme selection
    theme = st.selectbox(
        "Select Theme",
        options=get_available_themes(),
        index=0
    )
    
    # Additional settings
    st.markdown("### Additional Settings")
    
    # Style settings
    st.markdown("#### Style Settings")
    default_style = get_default_style()
    
    # Create expandable sections for each style category
    for category, settings in default_style.items():
        with st.expander(f"{category.title()} Settings"):
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
    
    # Landcover settings
    st.markdown("#### Landcover Settings")
    default_landcover = get_default_landcover()
    
    for category, settings in default_landcover.items():
        with st.expander(f"{category.title()} Landcover"):
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

# Generate map button
if st.button("Generate Map"):
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
                
                # Download buttons
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
        st.warning("Please draw an area on the map first.") 