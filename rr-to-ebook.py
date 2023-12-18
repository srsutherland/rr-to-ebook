import os
import re
from bs4 import BeautifulSoup
import requests

# pylint: disable=redefined-outer-name

def sanitize_filename(filename: str) -> str:
    """Remove characters that are not allowed in filenames"""
    return re.sub(r'[<>:"/\\|?* ]', '_', filename)


def extract_id_from_url(url: str) -> str:
    """Extract the fiction id from the url"""
    # Use a regex to extract the fiction id
    # See sample_urls for examples
    re_string = r"https://www.royalroad.com/fiction/(\d+)(/|$).*"
    match = re.match(re_string, url)
    if match:
        return match.group(1)
    else:
        raise ValueError(f"Could not extract fiction id from url: {url}")


def get_canonical_fiction_url(fiction_id: str) -> str:
    """Get the canonical fiction url from the fiction_id"""
    if not isinstance(fiction_id, str):
        fiction_id = str(fiction_id)
    if not fiction_id.isdigit():
        raise ValueError(f"fiction_id must be a number, got {fiction_id}")
    pre_redirect_url = f"https://www.royalroad.com/fiction/{fiction_id}"
    # Now use requests to get the canonical url that the above url redirects to
    response = requests.get(pre_redirect_url, timeout=3)  # Add timeout argument
    canonical_url = response.url
    return canonical_url


def get_chapter_list(fiction_id: str) -> list[str, str]:
    """Get the chapter list from the fiction_id"""
    if not fiction_id.isdigit():
        raise ValueError(f"fiction_id must be a number, got {fiction_id}")
    # Get the chapter list
    chapter_name_and_url_list = []
    url = f"https://www.royalroad.com/fiction/{fiction_id}"
    response = requests.get(url, timeout=3)  # Add timeout argument
    soup = BeautifulSoup(response.text, 'html.parser')
    for chapter_row in soup.find_all('tr', class_='chapter-row'):
        # first anchor has the chapter name
        anchor = chapter_row.find('a')
        if anchor.get('href') is not None:
            chapter_name_and_url_list.append(
                (anchor.text.strip(), anchor.get('href'))
            )
    return chapter_name_and_url_list


def get_chapter_html(chapter_url: str) -> str:
    """Get the chapter text from the chapter_url"""
    if not chapter_url.startswith("https://www.royalroad.com/fiction/"):
        if chapter_url.startswith("/fiction/"):
            chapter_url = "https://www.royalroad.com" + chapter_url
        else:
            raise ValueError(f"relative chapter_url must start with /fiction/, got {chapter_url}")
    response = requests.get(chapter_url, timeout=3)
    soup = BeautifulSoup(response.text, 'html.parser')
    chapter_content = soup.find('div', class_='chapter-inner chapter-content')
    return chapter_content.prettify()


if __name__ == '__main__':
    sample_fiction = "https://www.royalroad.com/fiction/25225/delve"
    output_folder = "output"
    
    # Test extract_id_from_url
    sample_fiction_id  = "25225"
    sample_urls = [
        "https://www.royalroad.com/fiction/25225",
        "https://www.royalroad.com/fiction/25225/",
        "https://www.royalroad.com/fiction/25225/delve",
        "https://www.royalroad.com/fiction/25225/delve/",
        "https://www.royalroad.com/fiction/25225/delve/chapter/368012/001-woodland",
        "https://www.royalroad.com/fiction/25225/delve/chapter/368012/001-woodland/",
    ]
    for s_url in sample_urls:
        assert extract_id_from_url(s_url) == sample_fiction_id
    
    # Urls with special formatting:
    ## /fiction/25225/delve/chapter/550244/111-pickup
    ## /fiction/25225/delve/chapter/439467/069-hangover
    
    # Test chapter download
    sample_canonical_url = get_canonical_fiction_url(sample_fiction_id)
    print(f"Canonical fiction url: {sample_canonical_url}")
    chapter_list = get_chapter_list(sample_fiction_id)
    if output_folder is not None:
        folder_name = sample_canonical_url[sample_canonical_url.find(sample_fiction_id):]
        output_folder = "output/" + folder_name.replace("/", "_")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for chapter in chapter_list:
        name, url = chapter
        print(f"{name}\t\t{url}")
        # save the chapter to a file
        chapter_html = get_chapter_html(url)
        sanitized_name = sanitize_filename(name)
        output_file = f"{output_folder}/{sanitized_name}.html"
        with open(output_file, 'w', encoding="utf-8") as f:
            f.write(chapter_html)
        print(f"Saved chapter to {output_file}")
