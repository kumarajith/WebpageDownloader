from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import argparse
import json
import os
import requests
import validators

USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36'}
METADATA_FILENAME = 'metadata.json'
POPULAR_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.js', '.css')
ASSET_TAG_ATTRIBUTES = {
    'img': 'src',
    'script': 'src',
    'link': 'href'
}

def is_valid_url(url):
    """
    Validates the provided URL.
    
    Args:
        url (str): The URL to be validated.

    Returns:
        bool: True if the url is valid 
    """
    return validators.url(url)


def download(urls):
    """
    Iterates through urls, downloads webpages and stores metadata.
    
    Args:
        urls (list of str): List of URLs to be downloaded.
    """
    for url in urls:
        if not is_valid_url(url): 
            print(f'Invalid url: {url}')
            continue

        response = requests.get(url, headers=USER_AGENT_HEADER) # User agent to ensure requests dont fail
        if response.status_code != 200:
            print(f'''Failed to download url: {url}; Status code: {response.status_code}''')
            continue
        
        link_count = get_number_of_links(response.content)
        content = download_assets(url, response.content)
        file_name = os.path.basename(url)
        with open(f'{file_name}.html', 'wb') as file:
            file.write(content.encode('utf-8'))
        
        store_metadata(file_name, {'links': link_count})


def get_number_of_links(content):
    """
    Iterates through webpage content and gets the number of links.
    
    Args:
        content (str): HTML content.

    Returns:
        int: Number of links on the webpage
    """
    soup = BeautifulSoup(content, 'html.parser')
    assets = soup.find_all('a')
    count = 0
    for asset in assets:
        if asset.get('href'):
            count += 1
            
    return count
    

def download_assets(url, content):
    """
    Download assets from the webpage.

    Args:
        url (str): URL of the webpage.
        content (str): HTML content.

    Returns:
        int: Number of links on the webpage
    """
    soup = BeautifulSoup(content, 'html.parser')
    assets = soup.find_all(ASSET_TAG_ATTRIBUTES.keys())
    base_url = url
    base_tag = soup.find('base')
    directory = os.path.basename(url)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if base_tag and base_tag.get('href'):
        base_url = base_tag['href']
        
    for asset in assets:
        link_attribute = ASSET_TAG_ATTRIBUTES[asset.name]
        if not asset.get(link_attribute):
            continue

        asset_url = asset[link_attribute]
        full_url = urljoin(base_url, asset_url)
        file_name = os.path.basename(full_url).split('?', 1)[0] # Remove any query params
        if not (file_name.endswith(POPULAR_EXTENSIONS)):
            continue

        response = requests.get(full_url)
        if response.status_code != 200:
            continue
        
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)

        asset[link_attribute] = file_path # Update link to local files

    return str(soup)

def store_metadata(url, new_metadata):
    """
    Store metadata for downloaded webpages.

    Args:
        url (str): URL of the webpage.
        new_metadata (dict): Metadata to be stored.
    """
    metadata = read_metadata_file()

    new_metadata['site'] = url
    new_metadata['last_fetch'] = str(datetime.now())
    metadata[url] = new_metadata

    with open(METADATA_FILENAME, 'w') as file:
        json.dump(metadata, file, indent=2)


def read_metadata_file():
    """
    Open the metadata file and return all data

    Returns:
        dict: Metadata stored in the file.
    """
    if not os.path.exists(METADATA_FILENAME):
        with open(METADATA_FILENAME, 'w') as file:
            json.dump({}, file)

    with open(METADATA_FILENAME, 'r') as file:
        metadata = json.load(file)

    return metadata

def fetch_metadata(urls):
    """
    Fetch and display stored metadata for downloaded webpages.

    Args:
        urls (list of str): List of URLs for metadata to be fetched.
    """
    metadata = read_metadata_file()
    for url in urls:
        base_url = os.path.basename(url)
        if base_url not in metadata:
            print(f'Data not found for url: {url}')
            continue
        
        print(metadata[base_url])
    

def main():
    """
    Main function to parse command line arguments and execute actions.
    """
    parser = argparse.ArgumentParser(description='Download websites.')
    parser.add_argument('urls', nargs='+', help='URLs to download')
    parser.add_argument('--metadata', action='store_true', help='')
    args = parser.parse_args()
    if args.metadata:
        fetch_metadata(args.urls)
    else:        
        download(args.urls)


if __name__ == '__main__':
    main()
