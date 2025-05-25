# Prettymapp Generator

A Streamlit web application for generating beautiful maps from OpenStreetMap data using an interactive map interface.

## Features

- Interactive map interface for drawing areas
- Multiple theme options
- Customizable style settings
- Customizable landcover settings
- Download generated maps as PNG images
- Download map data as GeoJSON files

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd prettymapRevamped
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Use the interactive map to draw an area:
   - Use the drawing tools in the top-left corner of the map
   - Draw a rectangle or circle to define your area of interest

4. Configure the map settings:
   - Select a theme from the dropdown menu
   - Customize style settings in the expandable sections
   - Customize landcover settings in the expandable sections

5. Click "Generate Map" to create your map

6. Download the generated map and data:
   - Use the "Download Map Image" button to save the map as a PNG file
   - Use the "Download Map Data" button to save the map data as a GeoJSON file

## Requirements

See `requirements.txt` for a complete list of dependencies.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 