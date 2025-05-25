import os
import json
from typing import Dict, Any, List, Tuple
import geopandas as gpd
from shapely.geometry import Polygon, shape, mapping, box
from prettymapp.geo import get_aoi
from prettymapp.osm import get_osm_geometries
from prettymapp.plotting import Plot
from prettymapp.settings import STYLES, LANDCOVER_CLASSES
import numpy as np

def get_available_themes() -> List[str]:
    """Get list of available themes."""
    return list(STYLES.keys())

def get_default_style() -> Dict[str, Any]:
    """Get default style settings."""
    return STYLES["Peach"].copy()

def get_default_landcover() -> Dict[str, Any]:
    """Get default landcover settings."""
    return LANDCOVER_CLASSES.copy()

def determine_utm_crs(geometry):
    """Determine the appropriate UTM CRS for a given geometry."""
    # Convert geometry to GeoDataFrame if it's not already
    if isinstance(geometry, dict):
        geom = shape(geometry)
    else:
        geom = geometry
    
    # Get the centroid of the geometry
    centroid = geom.centroid
    
    # Calculate UTM zone
    lon = centroid.x
    lat = centroid.y
    
    # UTM zone calculation
    zone_number = int((lon + 180) / 6) + 1
    
    # Determine hemisphere
    hemisphere = 'N' if lat >= 0 else 'S'
    
    # Create UTM CRS string
    utm_crs = f'EPSG:326{zone_number:02d}' if hemisphere == 'N' else f'EPSG:327{zone_number:02d}'
    
    return utm_crs

def generate_map(
    geometry: Dict[str, Any],
    style: str = "Peach",
    custom_settings: Dict[str, Any] = None,
    custom_landcover: Dict[str, Any] = None
) -> Tuple[Plot, gpd.GeoDataFrame]:
    """Generate a prettymap from the given geometry."""
    try:
        # Convert geometry to shapely if it's a dict
        if isinstance(geometry, dict):
            geom = shape(geometry)
        else:
            geom = geometry
        
        # Get bounds
        minx, miny, maxx, maxy = geom.bounds
        
        # Create a box geometry from bounds
        bbox = box(minx, miny, maxx, maxy)
        
        # Determine UTM CRS
        utm_crs = determine_utm_crs(bbox)
        
        # Get OSM geometries
        df = get_osm_geometries(aoi=bbox, landcover_classes=custom_landcover)
        
        # Project to UTM CRS
        df = df.to_crs(utm_crs)
        
        # Create plot
        fig = Plot(
            df=df,
            aoi_bounds=[minx, miny, maxx, maxy],
            draw_settings=STYLES[style] if custom_settings is None else custom_settings
        )
        
        return fig, df
        
    except Exception as e:
        raise Exception(f"Error generating map: {str(e)}")

def save_map_data(df: gpd.GeoDataFrame, filename: str) -> str:
    """Save map data to GeoJSON file."""
    df.to_file(filename, driver='GeoJSON')
    return filename 