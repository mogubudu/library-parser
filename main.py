import os
import requests

path_to_save = 'books'
os.makedirs(path_to_save, exist_ok=True)

for book_id in range(1, 11):
    url = f'http://tululu.org/txt.php?id={book_id}'

    response = requests.get(url)
    response.raise_for_status()

    filename = f'id{book_id}'

    with open(f'{path_to_save}/{filename}', 'wb') as file:
        file.write(response.content)