# Wikipedia Coordinate Extractor

A Python tool for extracting geographical coordinates and addresses from Wikipedia articles.

## Overview

This script extracts location data from Wikipedia pages using multiple methods:
1. Direct coordinate extraction from various HTML elements
2. Address extraction from infoboxes
3. Geocoding of detailed addresses to coordinates when direct coordinates aren't available

The tool works with both English and Finnish Wikipedia pages and can be extended to support other languages.

## Features

- **Multiple Extraction Methods**: Uses 6 different methods to find coordinates in Wikipedia pages
- **Address Fallback**: When coordinates aren't found, extracts addresses as fallback
- **Geocoding**: Converts detailed addresses to coordinates using OpenStreetMap's Nominatim API
- **Citation Cleaning**: Removes Wikipedia citation markers ([1], [2], etc.) from addresses
- **Progress Tracking**: Real-time progress counter with ETA
- **Detailed Statistics**: Tracks success rates of different extraction methods
- **Polite Scraping**: Includes delays to respect Wikipedia's and Nominatim's rate limits

## Requirements

- Python 3.6+
- Required libraries:
  - requests
  - beautifulsoup4
  - json (standard library)
  - re (standard library)
  - time (standard library)
  - random (standard library)
  - argparse (standard library)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/wikipedia-coordinate-extractor.git
   cd wikipedia-coordinate-extractor
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

The script can be used in two modes:

### 1. Process a batch of articles

```
python main.py batch input.json output.json
```

- `input.json`: A JSON file containing a list of articles with their Wikipedia links
- `output.json`: The output file where results will be saved

Example input.json format:
```json
[
  {
    "name": "Helsinki Cathedral",
    "wikipedia_link": "https://en.wikipedia.org/wiki/Helsinki_Cathedral"
  },
  {
    "name": "Turku Castle",
    "wikipedia_link": "https://fi.wikipedia.org/wiki/Turun_linna"
  }
]
```

### 2. Test a single Wikipedia URL

```
python main.py url "https://en.wikipedia.org/wiki/Helsinki_Cathedral"
```

## Coordinate Extraction Methods

The script tries the following methods in sequence:

1. **Method 1**: Extract from span with id="coordinatespan"
2. **Method 2**: Extract from mw-indicator with id="mw-indicator-AA-coordinates"
3. **Method 3**: Extract from the infobox table coordinates row
4. **Method 4**: Extract from script containing wgCoordinates variable
5. **Method 5**: Extract from metadata and geo microformat tags
6. **Method 6**: Extract from Kartographer map data or HTML map elements

If all methods fail, it tries to extract an address and geocode it if the address is detailed enough.

## Output Format

The script adds coordinates and/or address information to each article in the input JSON:

```json
{
  "name": "Helsinki Cathedral",
  "wikipedia_link": "https://en.wikipedia.org/wiki/Helsinki_Cathedral",
  "coordinates": {
    "lat": 60.17045,
    "lon": 24.95189,
    "format": "decimal",
    "original": "60°10′14″N 24°57′07″E",
    "method": "method_1"
  }
}
```

## Additional Notes

- The script skips articles that already have coordinates.
- Progress is saved periodically (every 10 articles) to prevent data loss.
- The script includes random delays to be respectful to Wikipedia and Nominatim servers.
- Address extraction includes cleaning of citation markers to improve geocoding success.

## Extending to Other Languages

The script currently supports English and Finnish Wikipedia pages. To add support for another language:

1. Update the address and coordinate extraction to look for the corresponding terms in your language.
2. Add appropriate language codes to the Accept-Language header in the geocoding function.

## License

[MIT License](LICENSE)

## Acknowledgements

- [OpenStreetMap Nominatim](https://nominatim.org/) for geocoding services
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
