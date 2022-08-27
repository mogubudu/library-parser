import os
import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urlparse, unquote, urljoin

def check_for_redirect(response):
    status_code = response.history[0].status_code
    response_url = response.url

    if status_code == 301 and response_url == 'https://tululu.org/':
        raise requests.HTTPError()


def get_filename(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    title_tag = soup.find('h1')
    title_tag = title_tag.text
    book_name = title_tag.split('::')[0].strip(' ')
    author = title_tag.split('::')[1].strip(' ')

    return f'{book_name} - {author}'

def get_image_url(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')

    image_src = soup.find('div', class_='bookimage').find('a').find('img')['src']
    return urljoin('https://tululu.org/',image_src)


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    
    filename = sanitize_filename(filename)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)

    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)

    return filepath

def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status

    os.makedirs(folder, exist_ok=True)

    path = urlparse(url).path
    path = unquote(path)
    
    filename = os.path.basename(path)
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, filename)

    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)

def get_comments(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')
    comments = soup.find_all('div', class_='texts')
    text_comments = []

    for comment in comments:
        text_comments += comment.find('span', class_='black')
    
    return text_comments


def download_comments(url, folder='comments/'):
    response = requests.get(url)
    response.raise_for_status

    os.makedirs(folder, exist_ok=True)
    filename = get_filename(url)
    filename = sanitize_filename(filename)





if __name__ == "__main__":
    
    for book_id in range(1, 11):
        book_url = f'http://tululu.org/b{book_id}/'
        download_url = f'http://tululu.org/txt.php?id={book_id}'

        response = requests.get(download_url)
        response.raise_for_status()

        try:
            check_for_redirect(response)
        except requests.HTTPError:
            continue

        filename = get_filename(book_url)
        
        image_url = get_image_url(book_url)
        print(get_comments(book_url))
