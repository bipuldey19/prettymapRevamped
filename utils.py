import json
from typing import Dict, Any, List, Tuple
import geopandas as gpd
from shapely.geometry import Polygon, shape, mapping, box
from prettymapp.geo import get_aoi
from prettymapp.osm import get_osm_geometries
from prettymapp.plotting import Plot
from prettymapp.settings import STYLES, LANDCOVER_CLASSES

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
    # Convert GeoJSON to Shapely geometry
    geom = shape(geometry)
    
    # Get bounds from geometry
    minx, miny, maxx, maxy = geom.bounds

    # Calculate the centroid of the geometry
    centroid = geom.centroid
    lon, lat = centroid.x, centroid.y
    
    # Create a box geometry from bounds
    bbox = box(minx, miny, maxx, maxy)
    
    # Get OSM geometries using the bounds and centroid for CRS determination
    landcover = custom_landcover if custom_landcover else get_default_landcover()
    df = get_osm_geometries(
        aoi=bbox,
        landcover_classes=landcover,
        center=(lat, lon) # Pass centroid coordinates
    )
    
    # Get style settings
    draw_settings = STYLES[style].copy()
    if custom_settings:
        draw_settings.update(custom_settings)
    
    # Prepare plotting parameters for the Plot constructor based on example
    plot_params = {
        "df": df,
        "aoi_bounds": [minx, miny, maxx, maxy],
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