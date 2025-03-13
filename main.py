#!/usr/bin/env python3
# Wikipedia Coordinate Extractor
# Extracts coordinates and addresses from Wikipedia articles

import json
import re
import time
import random
import argparse
import requests
from bs4 import BeautifulSoup


def load_data(input_file):
    """
    Load articles from JSON file
    
    Args:
        input_file (str): Path to input JSON file
        
    Returns:
        list: List of article dictionaries
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: File {input_file} is not valid JSON.")
        return []


def save_data(articles, output_file):
    """
    Save articles with coordinates to JSON file
    
    Args:
        articles (list): List of article dictionaries
        output_file (str): Path to output JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print(f"Results saved to {output_file}")


def fetch_page(url):
    """
    Fetch Wikipedia page with polite delay to avoid hitting rate limits
    
    Args:
        url (str): Wikipedia URL to fetch
        
    Returns:
        BeautifulSoup: Parsed HTML or None if request failed
    """
    # Random delay between 1-3 seconds to be polite to Wikipedia
    time.sleep(random.uniform(1, 3))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def dms_to_decimal(dms_str):
    """
    Convert coordinates from DMS (Degrees, Minutes, Seconds) to decimal degrees
    
    Args:
        dms_str (str): DMS string like 60°09′33.2″N
        
    Returns:
        float: Decimal degrees or None if parsing failed
    """
    direction = dms_str[-1]
    dms_str = dms_str[:-1]  # Remove direction
    
    # Split the string into degrees, minutes, and seconds
    parts = re.findall(r'(\d+)°(\d+)′(\d+(?:\.\d+)?)″', dms_str)
    
    if parts:
        degrees, minutes, seconds = map(float, parts[0])
        decimal = degrees + minutes/60 + seconds/3600
        
        # Adjust sign based on direction
        if direction in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    
    return None


def extract_coordinates_method_1(soup):
    """
    Method 1: Extract coordinates from the span with id="coordinatespan"
    Example: <span id="coordinatespan" class="plainlinksneverexpand">...
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Coordinate dictionary or None if not found
    """
    coord_span = soup.find('span', id='coordinatespan')
    if not coord_span:
        return None
    
    # Look for the actual coordinate text
    coord_text = coord_span.get_text().strip()
    
    # Extract latitude and longitude using regex
    lat_match = re.search(r'(\d+°\d+′\d+(?:\.\d+)?″[NS])', coord_text)
    lon_match = re.search(r'(\d+°\d+′\d+(?:\.\d+)?″[EW])', coord_text)
    
    if lat_match and lon_match:
        lat_dms = lat_match.group(1)
        lon_dms = lon_match.group(1)
        
        # Convert DMS to decimal degrees
        lat_decimal = dms_to_decimal(lat_dms)
        lon_decimal = dms_to_decimal(lon_dms)
        
        return {
            "lat": lat_decimal,
            "lon": lon_decimal,
            "format": "DMS",
            "original": f"{lat_dms}, {lon_dms}",
            "method": "method_1"
        }
    
    # Alternative format: decimal degrees
    decimal_match = re.search(r'(\d+\.\d+)°[NS].*?(\d+\.\d+)°[EW]', coord_text)
    if decimal_match:
        lat = float(decimal_match.group(1))
        lon = float(decimal_match.group(2))
        
        # Check if we need to negate based on direction
        if 'S' in coord_text:
            lat = -lat
        if 'W' in coord_text:
            lon = -lon
        
        return {
            "lat": lat,
            "lon": lon,
            "format": "decimal",
            "original": coord_text,
            "method": "method_1"
        }
    
    return None


def extract_coordinates_method_2(soup):
    """
    Method 2: Extract coordinates from the mw-indicator with id="mw-indicator-AA-coordinates"
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Coordinate dictionary or None if not found
    """
    indicator = soup.find('div', id='mw-indicator-AA-coordinates')
    if not indicator:
        return None
    
    coord_span = indicator.find('span', id='coordinatespan')
    if not coord_span:
        return None
    
    # Extract the text from the span
    coord_text = coord_span.get_text().strip()
    
    # Extract latitude and longitude using regex
    lat_match = re.search(r'(\d+°\d+′\d+(?:\.\d+)?″[NS])', coord_text)
    lon_match = re.search(r'(\d+°\d+′\d+(?:\.\d+)?″[EW])', coord_text)
    
    if lat_match and lon_match:
        lat_dms = lat_match.group(1)
        lon_dms = lon_match.group(1)
        
        # Convert DMS to decimal degrees
        lat_decimal = dms_to_decimal(lat_dms)
        lon_decimal = dms_to_decimal(lon_dms)
        
        return {
            "lat": lat_decimal,
            "lon": lon_decimal,
            "format": "DMS",
            "original": f"{lat_dms}, {lon_dms}",
            "method": "method_2"
        }
    
    return None


def extract_coordinates_method_3(soup):
    """
    Method 3: Extract coordinates from the infobox table coordinates row
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Coordinate dictionary or None if not found
    """
    # Find the infobox table
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        return None
    
    # Find the row with "Koordinaatit" label
    coord_row = None
    for row in infobox.find_all('tr'):
        th = row.find('th')
        if th and 'Koordinaatit' in th.get_text():
            coord_row = row
            break
    
    if not coord_row:
        return None
    
    # Get the coordinate text from the td
    td = coord_row.find('td')
    if not td:
        return None
    
    coord_span = td.find('span', id='coordinatespan')
    if not coord_span:
        return None
    
    # Extract the text
    coord_text = coord_span.get_text().strip()
    
    # Extract latitude and longitude using regex
    lat_match = re.search(r'(\d+°\d+′\d+(?:\.\d+)?″[NS])', coord_text)
    lon_match = re.search(r'(\d+°\d+′\d+(?:\.\d+)?″[EW])', coord_text)
    
    if lat_match and lon_match:
        lat_dms = lat_match.group(1)
        lon_dms = lon_match.group(1)
        
        # Convert DMS to decimal degrees
        lat_decimal = dms_to_decimal(lat_dms)
        lon_decimal = dms_to_decimal(lon_dms)
        
        return {
            "lat": lat_decimal,
            "lon": lon_decimal,
            "format": "DMS",
            "original": f"{lat_dms}, {lon_dms}",
            "method": "method_3"
        }
    
    return None


def extract_coordinates_method_4(soup):
    """
    Method 4: Extract coordinates from the script section containing wgCoordinates
    Example: "wgCoordinates":{"lat":61.29861666666667,"lon":25.681866666666668}
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Coordinate dictionary or None if not found
    """
    # Look for script tags
    script_tags = soup.find_all('script')
    
    for script in script_tags:
        if script.string:
            # Search for wgCoordinates in the script content
            coords_match = re.search(r'"wgCoordinates":\s*{\s*"lat":\s*([\d\.-]+),\s*"lon":\s*([\d\.-]+)\s*}', script.string)
            if coords_match:
                lat = float(coords_match.group(1))
                lon = float(coords_match.group(2))
                
                return {
                    "lat": lat,
                    "lon": lon,
                    "format": "decimal",
                    "original": f"wgCoordinates: {lat}, {lon}",
                    "method": "method_4"
                }
    
    return None


def extract_coordinates_method_5(soup):
    """
    Method 5: Extract coordinates from metadata (Coordinates tag in head section)
    Some pages have coordinates in meta tags rather than in the visible content
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Coordinate dictionary or None if not found
    """
    # First check if there's a meta tag with geo position
    meta_geo = soup.find('meta', attrs={'name': 'geo.position'})
    if meta_geo and meta_geo.get('content'):
        content = meta_geo.get('content')
        coords = content.split(';')
        if len(coords) == 2:
            try:
                lat = float(coords[0].strip())
                lon = float(coords[1].strip())
                return {
                    "lat": lat,
                    "lon": lon,
                    "format": "decimal",
                    "original": f"meta geo.position: {content}",
                    "method": "method_5"
                }
            except ValueError:
                pass
    
    # Look for hidden spans with geo microformat
    geo_span = soup.find('span', class_='geo')
    if geo_span:
        coords_text = geo_span.get_text().strip()
        coords_match = re.match(r'([\d\.-]+);\s*([\d\.-]+)', coords_text)
        if coords_match:
            try:
                lat = float(coords_match.group(1))
                lon = float(coords_match.group(2))
                return {
                    "lat": lat,
                    "lon": lon,
                    "format": "decimal",
                    "original": f"geo microformat: {coords_text}",
                    "method": "method_5"
                }
            except ValueError:
                pass
    
    return None

def extract_coordinates_method_6(soup):
    """
    Method 6: Extract coordinates from Kartographer map data or HTML map elements
    with data-lat and data-lon attributes
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        dict: Coordinate dictionary or None if not found
    """
    # Look for HTML map elements with data-lat and data-lon attributes
    map_element = soup.find(attrs={"data-lat": True, "data-lon": True})
    if map_element:
        try:
            lat = float(map_element.get("data-lat"))
            lon = float(map_element.get("data-lon"))
            return {
                "lat": lat,
                "lon": lon,
                "format": "decimal",
                "original": f"map element: data-lat={lat}, data-lon={lon}",
                "method": "method_6"
            }
        except (ValueError, TypeError):
            pass
    
    # Look for Kartographer JSON data in scripts
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and "wgKartographerLiveData" in script.string:
            # Try to extract coordinates using regex
            coords_match = re.search(r'"coordinates":\s*\[([\d\.-]+),\s*([\d\.-]+)\]', script.string)
            if coords_match:
                try:
                    # Note: Kartographer sometimes uses [lon, lat] order instead of [lat, lon]
                    lon = float(coords_match.group(1))
                    lat = float(coords_match.group(2))
                    return {
                        "lat": lat,
                        "lon": lon,
                        "format": "decimal",
                        "original": f"Kartographer data: {lon}, {lat}",
                        "method": "method_6"
                    }
                except (ValueError, TypeError):
                    pass
    
    return None

def extract_address(soup):
    """
    Extract address from the infobox
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        str: Address or None if not found
    """
    # Find the infobox table
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        return None
    
    # Look for "Sijainti" (Location) row
    address = None
    
    # Method 1: Standard format - look for th/td with "Sijainti" text
    for row in infobox.find_all('tr'):
        header = row.find(['th', 'td'], string=lambda text: text and 'Sijainti' in text)
        if header:
            td = row.find('td', recursive=False) if header.name == 'th' else header.find_next('td')
            if td:
                address = td.get_text().strip()
                # Clean up the address
                address = re.sub(r'\s+', ' ', address)
                print(f"  - Found address using method 1: {address}")
                break
    
    # Method 2: Alternative format - look for "font-weight:bold" style in td
    if not address:
        for row in infobox.find_all('tr'):
            td = row.find('td', style=lambda style: style and 'font-weight:bold' in style)
            if td and 'Sijainti' in td.get_text():
                value_td = td.find_next('td')
                if value_td:
                    address = value_td.get_text().strip()
                    address = re.sub(r'\s+', ' ', address)
                    print(f"  - Found address using method 2: {address}")
                    break
    
    # If we found an address, check if it's a detailed one
    if address:
        # Check if it has both a street number and a city (comma separated)
        has_street_number = bool(re.search(r'\d+', address))
        has_comma = ',' in address
        
        is_detailed = has_street_number and has_comma
        
        return {
            "text": address,
            "detailed": is_detailed
        }
    
    return None


def extract_all_coordinates(soup):
    """
    Try all methods to extract coordinates
    
    Args:
        soup (BeautifulSoup): Parsed HTML
        
    Returns:
        tuple: (coordinates dict or None, method stats dictionary)
    """
    method_stats = {
        "method_1": 0,
        "method_2": 0,
        "method_3": 0,
        "method_4": 0,
        "method_5": 0,
        "method_6": 0,
        "no_coords": 0,
        "address_found": 0,
        "detailed_address": 0
    }
    
    # Try all methods in sequence
    methods = [
        (extract_coordinates_method_1, "method_1"),
        (extract_coordinates_method_2, "method_2"),
        (extract_coordinates_method_3, "method_3"),
        (extract_coordinates_method_4, "method_4"),
        (extract_coordinates_method_5, "method_5"),
        (extract_coordinates_method_6, "method_6")
    ]
    
    for method_func, method_name in methods:
        coords = method_func(soup)
        if coords:
            method_stats[method_name] += 1
            return coords, method_stats
    
    # If we get here, no coordinates were found
    method_stats["no_coords"] += 1
    return None, method_stats


def process_article(article, verbose=True):
    """
    Process a single article to extract coordinates and address
    
    Args:
        article (dict): Article dictionary with name and wikipedia_link
        verbose (bool): Whether to print detailed information
        
    Returns:
        dict: Updated article with coordinates and/or address
    """
    if verbose:
        print(f"\nProcessing: {article['name']}")
    
    url = article['wikipedia_link']
    soup = fetch_page(url)
    
    if not soup:
        print(f"  - Failed to fetch page for {article['name']}")
        return article
    
    # Extract coordinates
    coords, method_stats = extract_all_coordinates(soup)
    
    if coords:
        if verbose:
            print(f"  - Found coordinates using {coords['method']}: {coords['lat']}, {coords['lon']}")
        article['coordinates'] = coords
    else:
        if verbose:
            print(f"  - No coordinates found for {article['name']}")
        
        # If we couldn't find coordinates, try to get the address as a fallback
        address_info = extract_address(soup)
        if address_info:
            method_stats["address_found"] += 1
            article['address'] = address_info['text']
            
            if address_info['detailed']:
                method_stats["detailed_address"] += 1
                if verbose:
                    print(f"  - Found detailed address as fallback: {address_info['text']}")
            else:
                if verbose:
                    print(f"  - Found address as fallback (not detailed): {address_info['text']}")
        else:
            if verbose:
                print(f"  - No address found as fallback for {article['name']}")
    
    return article, method_stats


def process_articles(input_file, output_file, verbose=True):
    """
    Main function to process all articles
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
        verbose (bool): Whether to print detailed information
    """
    articles = load_data(input_file)
    if not articles:
        print("No articles loaded. Exiting.")
        return
    
    print(f"Processing {len(articles)} articles...")
    
    # Count how many articles already have coordinates
    already_with_coords = sum(1 for article in articles if article.get('coordinates'))
    already_with_address = sum(1 for article in articles if article.get('address'))
    
    print(f"Already have coordinates for {already_with_coords}/{len(articles)} articles.")
    print(f"Already have addresses for {already_with_address}/{len(articles)} articles.")
    
    # Initialize stats
    total_stats = {
        "method_1": 0,
        "method_2": 0,
        "method_3": 0,
        "method_4": 0,
        "method_5": 0,
        "method_6": 0,
        "no_coords": 0,
        "address_found": 0,
        "detailed_address": 0
    }
    
    processed_count = 0
    skipped_count = 0
    
    for i, article in enumerate(articles):
        # Skip articles that already have coordinates
        if article.get('coordinates'):
            skipped_count += 1
            continue
            
        processed_count += 1
        
        updated_article, method_stats = process_article(article, verbose)
        articles[i] = updated_article
        
        # Update total stats
        for key in total_stats:
            total_stats[key] += method_stats.get(key, 0)
        
        # Save progress periodically
        if (i + 1) % 10 == 0:
            print(f"  - Saving progress after {i + 1} articles...")
            save_data(articles, output_file)
    
    # Final save of all articles
    save_data(articles, output_file)
    
    # Print summary
    with_coords = sum(1 for article in articles if article.get('coordinates'))
    with_address = sum(1 for article in articles if article.get('address'))
    
    print("\nSummary:")
    print(f"- Total articles: {len(articles)}")
    print(f"- Processed articles: {processed_count}")
    print(f"- Skipped articles (already had coordinates): {skipped_count}")
    print(f"- Articles with coordinates: {with_coords} ({with_coords/len(articles)*100:.1f}%)")
    print(f"- Articles with address: {with_address} ({with_address/len(articles)*100:.1f}%)")
    
    # Print method statistics (only for processed articles)
    if processed_count > 0:
        print("\nCoordinate Extraction Method Statistics (for processed articles):")
        print(f"- Method 1 (span id='coordinatespan'): {total_stats['method_1']} successes")
        print(f"- Method 2 (mw-indicator-AA-coordinates): {total_stats['method_2']} successes")
        print(f"- Method 3 (infobox table): {total_stats['method_3']} successes")
        print(f"- Method 4 (wgCoordinates in script): {total_stats['method_4']} successes")
        print(f"- Method 5 (geo metadata): {total_stats['method_5']} successes")
        print(f"- Method 5 (geo metadata): {total_stats['method_6']} successes")
        print(f"- No coordinates found: {total_stats['no_coords']} articles")
        
        print("\nAddress Extraction Statistics (for processed articles):")
        print(f"- Articles with address found: {total_stats['address_found']} articles")
        print(f"- Articles with detailed address found: {total_stats['detailed_address']} articles")


def test_single_url(url, verbose=True):
    """
    Test the coordinate and address extraction methods on a single URL
    
    Args:
        url (str): Wikipedia URL to test
        verbose (bool): Whether to print detailed information
        
    Returns:
        dict: Results with coordinates and address information
    """
    print(f"\n===== Testing Coordinate Extraction on {url} =====")
    
    article = {
        "name": url.split('/')[-1],
        "wikipedia_link": url
    }
    
    updated_article, _ = process_article(article, verbose)
    
    print("\nExtraction Results:")
    if 'coordinates' in updated_article:
        coords = updated_article['coordinates']
        print(f"- Coordinates: {coords['lat']}, {coords['lon']}")
        print(f"- Method: {coords['method']}")
        print(f"- Format: {coords['format']}")
        print(f"- Original: {coords['original']}")
    else:
        print("- No coordinates found")
    
    if 'address' in updated_article:
        print(f"- Address: {updated_article['address']}")
    else:
        print("- No address found")
    
    return updated_article


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Extract coordinates and addresses from Wikipedia pages')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Process batch of articles
    batch_parser = subparsers.add_parser('batch', help='Process a batch of articles')
    batch_parser.add_argument('input', help='Input JSON file path')
    batch_parser.add_argument('output', help='Output JSON file path')
    batch_parser.add_argument('-q', '--quiet', action='store_true', help='Suppress detailed output')
    
    # Test single URL
    url_parser = subparsers.add_parser('url', help='Test a single Wikipedia URL')
    url_parser.add_argument('url', help='Wikipedia URL to test')
    
    args = parser.parse_args()
    
    if args.command == 'batch':
        process_articles(args.input, args.output, not args.quiet)
    elif args.command == 'url':
        test_single_url(args.url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()