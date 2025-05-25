import json
from typing import Dict, Any, List, Tuple
import geopandas as gpd
from shapely.geometry import Polygon, shape, mapping, box
from prettymapp.geo import get_aoi
from prettymapp.osm import get_osm_geometries
from prettymapp.plotting import Plot
from prettymapp.settings import STYLES, LANDCOVER_CLASSES
import streamlit as st
import folium
from streamlit_folium import st_folium
import tempfile
import os

def get_available_themes() -> List[str]:
    """Get list of available themes."""
    return list(STYLES.keys())

def get_default_style() -> Dict[str, Any]:
    """Get default style settings."""
    return STYLES["Peach"].copy()

def get_default_landcover() -> Dict[str, Any]:
    """Get default landcover settings."""
    return LANDCOVER_CLASSES.copy()

def generate_map(
    geometry: Dict[str, Any],
    style: str = "Peach",
    custom_settings: Dict[str, Any] = None,
    custom_landcover: Dict[str, Any] = None,
    plot_options: Dict[str, Any] = None
) -> Tuple[Plot, gpd.GeoDataFrame]:
    """Generate a prettymap from the given geometry."""
    # Convert GeoJSON to Shapely geometry (still useful for bounds)
    geom = shape(geometry)
    
    # Get bounds from geometry
    minx, miny, maxx, maxy = geom.bounds

    # Create AOI using get_aoi - Attempting to pass the raw GeoJSON dictionary
    aoi = None
    try:
        # Attempt 1: Pass the raw GeoJSON dictionary
        aoi = get_aoi(geometry) # Pass the original geometry dictionary
        st.info("Attempted to create AOI by passing the raw GeoJSON dictionary.")
    except Exception as e:
        st.error(f"Failed to create AOI by passing raw GeoJSON dictionary: {e}. Cannot proceed with map generation.")
        raise e # Re-raise the exception if AOI creation fails

    # Ensure AOI was successfully created before proceeding
    if aoi is None:
         st.error("Failed to create AOI.")
         raise Exception("Failed to create AOI.")
    
    # Get OSM geometries using the AOI object
    landcover = custom_landcover if custom_landcover else get_default_landcover()
    df = get_osm_geometries(
        aoi=aoi, # Pass the AOI object obtained from get_aoi
        landcover_classes=landcover
    )
    
    # Get style settings
    draw_settings = STYLES[style].copy()
    if custom_settings:
        draw_settings.update(custom_settings)
    
    # Prepare plotting parameters for the Plot constructor based on example
    plot_params = {
        "df": df,
        "aoi_bounds": [minx, miny, maxx, maxy], # Still pass bounds for plotting
        "draw_settings": draw_settings,
    }
    
    if plot_options:
        # Add plotting options to plot_params if they exist in plot_options
        if "shape" in plot_options:
            plot_params["shape"] = plot_options["shape"]
            
        if "bg_shape" in plot_options:
            plot_params["bg_shape"] = plot_options["bg_shape"]
        if "bg_color" in plot_options:
            plot_params["bg_color"] = plot_options["bg_color"]
        if "bg_buffer" in plot_options:
            plot_params["bg_buffer"] = plot_options["bg_buffer"]
            
        if "contour_color" in plot_options:
            plot_params["contour_color"] = plot_options["contour_color"]
        if "contour_width" in plot_options:
            plot_params["contour_width"] = plot_options["contour_width"]
            
        # Handle title settings based on display_title and example parameters
        plot_params["name_on"] = plot_options.get("display_title", False) # Use name_on for display toggle
        if plot_params["name_on"]:
            if "custom_title" in plot_options:
                 # Pass custom_title as text content if available, otherwise maybe prettymap uses a default?
                 # Let's try passing it as 'title' or 'text' if name_on is True. Based on previous errors, 'title' failed.
                 # Let's try passing the custom title text directly, maybe the param name is 'text'? Unsure.
                 # For now, let's focus on passing the known parameters from the example.
                 # The example has 'custom_title' and 'name_on', font_size, color, text_x/y/rotation
                 # It doesn't show custom_title passed to Plot(). Let's pass the known params first.
                 pass # Will handle text content parameter if we figure it out.

            if "text_size" in plot_options:
                plot_params["font_size"] = plot_options["text_size"] # Use font_size
            if "text_color" in plot_options:
                plot_params["font_color"] = plot_options["text_color"] # Use font_color
            if "text_x" in plot_options:
                plot_params["text_x"] = plot_options["text_x"]
            if "text_y" in plot_options:
                plot_params["text_y"] = plot_options["text_y"]
            if "text_rotation" in plot_options:
                plot_params["text_rotation"] = plot_options["text_rotation"]

    # print("Plotting parameters:", plot_params) # Keep for debugging if needed
    # Create plot
    fig = Plot(**plot_params)
    
    return fig, df

def save_map_data(df: gpd.GeoDataFrame, filename: str) -> str:
    """Save map data to GeoJSON file."""
    df.to_file(filename, driver='GeoJSON')
    return filename 

st.set_page_config(
    page_title="Prettymapp Generator",
    page_icon="🗺️",
    layout="centered"
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

# Initialize default settings
default_style = get_default_style()
default_landcover = get_default_landcover()

# Create a single column layout
col = st.container()

with col:
    st.subheader("Draw Area")
    # Create a map centered at a default location
    m = folium.Map(location=[0, 0], zoom_start=2)
    
    # Add drawing tools
    folium.plugins.Draw(
        export=False, # Set export to False to hide the button
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
        height=500, # Set a reasonable height
        # Removed width to let container handle horizontal sizing
        returned_objects=["last_active_drawing"]
    )
    
    # Update session state with drawn polygon
    if drawn_data and drawn_data.get("last_active_drawing"):
        st.session_state.drawn_polygon = drawn_data["last_active_drawing"]

    # Theme selection
    st.subheader("Theme")
    theme = st.selectbox(
        "Select Theme",
        options=get_available_themes(),
        index=0
    )
    
    # Plotting options
    st.subheader("Plotting Options")
    with st.expander("Customize Plot Appearance", expanded=False):
        # Map Shape
        map_shape = st.radio("Map Shape", options=["circle", "rectangle"], index=0)
        
        # Background Shape
        bg_shape = st.radio("Background Shape", options=["rectangle", "circle", "None"], index=0)
        
        # Background Color
        bg_color = st.color_picker("Background Color", value="#EAEAEA") # Default light gray
        
        # Background Size
        bg_size = st.slider("Background Size", min_value=0, max_value=50, value=2)
        
        # Map Contour Color
        contour_color = st.color_picker("Map Contour Color", value="#2F3034") # Default dark gray
        
        # Map Contour Width
        contour_width = st.slider("Map Contour Width", min_value=0, max_value=30, value=1)

        st.markdown("#### Title Settings")
        # Display Title
        display_title = st.checkbox("Display Title", value=True)
        
        # Custom Title
        custom_title = st.text_input("Custom Title (optional)", value="")
        
        if display_title:
            # Title Font Size
            title_font_size = st.slider("Title Font Size", min_value=1, max_value=50, value=25)
            
            # Title Font Color
            title_font_color = st.color_picker("Title Font Color", value="#2F3034") # Default dark gray
            
            # Title Position and Rotation - these are often relative, using sliders
            title_x = st.slider("Title X Position", min_value=-100, max_value=100, value=0)
            title_y = st.slider("Title Y Position", min_value=-100, max_value=100, value=0)
            title_rotation = st.slider("Title Rotation", min_value=-90, max_value=90, value=0)


    # Additional settings in expandable sections
    with st.expander("Style Settings", expanded=False):
        # Create columns for style settings (3 columns)
        style_cols = st.columns(3)
        for i, (category, settings) in enumerate(default_style.items()):
            with style_cols[i % 3]: # Use modulo 3 for column placement
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

    with st.expander("Landcover Settings", expanded=False):
        # Create columns for landcover settings (3 columns)
        landcover_cols = st.columns(3)
        for i, (category, settings) in enumerate(default_landcover.items()):
            with landcover_cols[i % 3]: # Use modulo 3 for column placement
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

    # Generate map button
    if st.button("Generate Map", use_container_width=True):
        if st.session_state.drawn_polygon:
            with st.spinner("Generating map..."):
                try:
                    # Collect plotting options
                    plot_options = {
                        "shape": map_shape,
                        "bg_shape": bg_shape if bg_shape != "None" else None,
                        "bg_color": bg_color,
                        "bg_buffer": bg_size, # prettymapp uses bg_buffer for size
                        "contour_color": contour_color,
                        "contour_width": contour_width,
                    }
                    
                    # Add title options if display_title is True, using parameter names from example
                    if display_title:
                        # The example shows custom_title for the text, but doesn't show it passed to Plot
                        # Let's pass the custom title as a parameter named 'title' for now, based on common practice,
                        # although previous errors suggest 'title' might not be the text content parameter.
                        # We will rely on the printout to confirm parameter names if this still fails.
                        # For now, pass known params from example + custom_title text with a likely name.
                        if custom_title:
                            plot_options["title"] = custom_title # Try 'title' for the text content
                        
                        plot_options["name_on"] = True # Explicitly set name_on based on checkbox
                        plot_options["font_size"] = title_font_size
                        plot_options["font_color"] = title_font_color
                        plot_options["text_x"] = title_x
                        plot_options["text_y"] = title_y
                        plot_options["text_rotation"] = title_rotation
                        
                    else:
                        plot_options["name_on"] = False # Explicitly set name_on based on checkbox
                        # If title is off, remove any potentially lingering title text parameter
                        plot_options.pop("title", None)

                    fig, df = generate_map(
                        geometry=st.session_state.drawn_polygon,
                        style=theme,
                        custom_settings=default_style,
                        custom_landcover=default_landcover,
                        plot_options=plot_options # Pass plotting options
                    )
                    st.session_state.map_fig = fig
                    st.session_state.map_data = df
                    
                    # Display the generated map
                    st.pyplot(fig.plot_all())
                    
                    # Download buttons in a single row
                    download_col1, download_col2 = st.columns(2)
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