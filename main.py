import os
import argparse
import requests

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urlparse, unquote, urljoin


def create_parser():
    parser = argparse.ArgumentParser(
            description='''
            Скрипт умеет скачивать книги и информацию о ней с сайта tululu.org
            '''
        )
    parser.add_argument('start_id',
                        type=int,
                        default=1,
                        nargs='?',
                        help='''
                        Указывается номер страницы с
                        которой начинаем скачивать книги
                        '''
                        )

    parser.add_argument('end_id',
                        type=int,
                        default=10,
                        nargs='?',
                        help='''Указывается номер последней
                        страницы для скачивания'''
                        )

    parser.add_argument('-bf', '--books_folder',
                        default='books/',
                        help='''Укажите папку в
                        которую нужно сохранить книги'''
                        )

    parser.add_argument('-if', '--images_folder',
                        default='images/',
                        help='''Укажите папку в которую
                        нужно сохранить обложки книг'''
                        )

    parser.add_argument('-cf', '--comments_folder',
                        default='comments/',
                        help='''Укажите папку в которую
                        нужно сохранить комментарии к книгам'''
                        )

    return parser


def check_for_redirect(response):
    if response.history and response.url == 'https://tululu.org/':
        raise requests.HTTPError('Обнаружен редирект. '
                                 'Книгу скачать не удалось.')


def download_txt(book_id, filename, folder='books/'):
    payload = {
        'id': book_id,
    }
    url = 'http://tululu.org/txt.php'

    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)

    filename = sanitize_filename(filename)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)

    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)

    return filepath


def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status
    check_for_redirect(response)

    os.makedirs(folder, exist_ok=True)

    path = urlparse(url).path
    path = unquote(path)

    filename = os.path.basename(path)
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, filename)

    with open(f'{filepath}', 'wb') as file:
        file.write(response.content)

    return filepath


def save_comments(comments, filename, folder='comments/'):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_filename(filename)
    filepath = os.path.join(folder, filename)

    if comments:
        with open(f'{filepath}', 'w', encoding="utf-8") as file:
            [file.write(f'\n {comment}') for comment in comments]

    return filepath


def parse_book_page(html_content):
    soup = BeautifulSoup(html_content, 'lxml')

    title_tag = soup.find('h1')
    title_tag = title_tag.text
    book_name, book_author = title_tag.split('::')
    book_name, book_author = book_name.strip(), book_author.strip()

    genres = [genre.text
              for genre in soup.find('span', class_='d_book')
              .find_all('a')]

    comments_html = soup.find_all('div', class_='texts')

    book_comments = [comment.find('span', class_='black').text
                     for comment in comments_html]

    image_src = (soup.find('div', class_='bookimage')
                 .find('a')
                 .find('img')['src'])

    book = {
        'book_author': book_author,
        'book_name': book_name,
        'book_genres': genres,
        'book_comments': book_comments,
        'image_src': image_src,
    }

    return book


if __name__ == "__main__":
    parser = create_parser()
    parse_args = parser.parse_args()

    start_id = parse_args.start_id
    end_id = parse_args.end_id

    books_folder = parse_args.books_folder
    images_folder = parse_args.images_folder
    comments_folder = parse_args.comments_folder

    for book_id in range(start_id, end_id):
        book_url = f'https://tululu.org/b{book_id}/'
        response = requests.get(book_url)

        try:
            response.raise_for_status()
            check_for_redirect(response)
        except requests.HTTPError as error:
            print(f'Ошибка для книги с ID {book_id}.', error)
            continue
        except requests.ConnectionError as error:
            print(f'Не удалось скачать книгу с ID {book_id}. '
                  f'Проверьте соединение с интернетом.', error)
            continue

        book = parse_book_page(response.text)
        filename = f"{book['book_name']} - {book['book_author']}"

        filepath = save_comments(
            book['book_comments'],
            f'Комментарии к книге {filename}'
        )
        print(f'Комментарии к книге {filename} успешно сохранены - {filepath}')

        try:
            filepath = download_txt(
                book_id,
                filename=filename,
                folder=books_folder
            )
            print(f'Книга {filename} успешно сохранена - {filepath}')
        except requests.HTTPError as error:
            print(f'Ошибка для книги с ID {book_id}.', error)
            continue
        except requests.ConnectionError as error:
            print(f'Не удалось скачать книгу с ID {book_id}. '
                  f'Проверьте соединение с интернетом.', error)
            continue

        image_url = urljoin(book_url, book['image_src'])

        try:
            filepath = download_image(image_url,
                                      folder=images_folder)
            print(f'Обложка книги {filename} успешно сохранена - {filepath}',
                  end='\n\n')
        except requests.HTTPError as error:
            print(f'Ошибка для изображения {image_url}.', error)
            continue
        except requests.ConnectionError as error:
            print(f'Ошибка для изображения {image_url}. '
                  f'Проверьте соединение с интернетом.', error)
            continue
