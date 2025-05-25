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
    custom_landcover: Dict[str, Any] = None
) -> Tuple[Plot, gpd.GeoDataFrame]:
    """Generate a prettymap from the given geometry."""
    # Convert GeoJSON to Shapely geometry
    geom = shape(geometry)
    
    # Get bounds from geometry
    minx, miny, maxx, maxy = geom.bounds
    
    # Create a box geometry from bounds
    bbox = box(minx, miny, maxx, maxy)
    
    # Get OSM geometries using the box geometry
    landcover = custom_landcover if custom_landcover else get_default_landcover()
    df = get_osm_geometries(
        aoi=bbox,
        landcover_classes=landcover
    )
    
    # Get style settings
    draw_settings = STYLES[style].copy()
    if custom_settings:
        draw_settings.update(custom_settings)
    
    # Create plot
    fig = Plot(
        df=df,
        aoi_bounds=[minx, miny, maxx, maxy],
        draw_settings=draw_settings,
    )
    
    return fig, df

def save_map_data(df: gpd.GeoDataFrame, filename: str) -> str:
    """Save map data to GeoJSON file."""
    df.to_file(filename, driver='GeoJSON')
    return filename 