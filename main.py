import os
import requests
import argparse

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urlparse, unquote, urljoin


def create_parser():
    parser = argparse.ArgumentParser(description='Скрипт умеет скачивать книги с сайта tululu.org')
    parser.add_argument('start_id', type=int, default=1, nargs='?', help='Указывается номер страницы с которой начинаем скачивать книги')
    parser.add_argument('end_id', type=int, default=10, nargs='?', help='Указывается номер последней страницы для скачивания')
 
    return parser


def check_for_redirect(response):
    status_code = response.history[0].status_code
    response_url = response.url

    if status_code == 301 and response_url == 'https://tululu.org/':
        raise requests.HTTPError()


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    
    filename = sanitize_filename(filename)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)

    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)


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


def parse_book_page(html_content):
    soup = BeautifulSoup(html_content, 'lxml')

    title_tag = soup.find('h1')
    title_tag = title_tag.text
    book_author, book_name = title_tag.split('::')[1], title_tag.split('::')[0]
    book_author, book_name = book_author.strip(), book_name.strip()

    genres = []
    
    for genre in soup.find('span', class_='d_book').find_all('a'):
        genres.append(genre.text)
    
    comments_html = soup.find_all('div', class_='texts')
    book_comments = []

    for comment in comments_html:
        book_comments.append(comment.find('span', class_='black').text)

    image_src = soup.find('div', class_='bookimage').find('a').find('img')['src']
    image_url = urljoin('https://tululu.org/', image_src)

    book_info = {
        'book_author': book_author,
        'book_name': book_name,
        'book_genres': genres,
        'book_comments': book_comments,
        'image_url': image_url,
    }

    return book_info


if __name__ == "__main__":
    parser = create_parser()
    parse_args = parser.parse_args()
    start_id = parse_args.start_id
    end_id = parse_args.end_id
    print(parse_args)

    for book_id in range(start_id, end_id):
        book_url = f'http://tululu.org/b{book_id}/'
        download_url = f'http://tululu.org/txt.php?id={book_id}'

        response = requests.get(book_url)
        response.raise_for_status()

        try:
            check_for_redirect(response)
        except requests.HTTPError:
            continue

        book = parse_book_page(response.text)
        #print(f'{book}')
