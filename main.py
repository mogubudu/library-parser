import os
import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

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


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    
    filename = sanitize_filename(filename)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)

    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)

    return filepath


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
        download_txt(download_url, filename)