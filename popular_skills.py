import requests
from decouple import config
import statistics
import logging


# RESUME_ID = '5ac8ff5aff0c81a0a40039ed1f437353764934' #analytic
RESUME_ID = 'aa1c78f6ff0d11fe040039ed1f385748785159' #techsup


class TokenManager:
    def __init__(self, access_token):
        self.access_token = access_token

    def get_header(self):
        return {'Authorization': f'Bearer {self.access_token}'}


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_suitable_vacancies(token_manager):
    page = 0
    count = 0

    per_page = 10
    # professional_role = 121 # techsup
    professional_role = 96 # developer
    vacancy_ids = []
    while page < 200:
        url = f'https://api.hh.ru/vacancies?per_page={per_page}&page={page}&professional_role={professional_role}&area=1'
        # url = f'https://api.hh.ru/resumes/{RESUME_ID}/similar_vacancies?per_page={per_page}&page={page}'
        headers = token_manager.get_header()
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            items = data['items']
            if len(items) == 0:
                logging.info(f'На странице {page} не найдено вакансий. Остановка цикла.')
                break
            for vacancy in items:
                count += 1
                if vacancy['id'] not in vacancy_ids:
                    vacancy_ids.append(vacancy['id'])

        logging.info(f'Обработана страница {page}. Всего найдено вакансий: {count}.')
        page += 1

    return vacancy_ids

def get_request():
    access_token = config('access_token')
    token_manager = TokenManager(access_token)
    ids = get_suitable_vacancies(token_manager)
    keywords = ['sql', 'postgre', 'python', 'linux', 'бд', 'база данных', 'базы данных', 'сетевые протоколы', 'restapi', 'http', 'линукс', 
                'мониторинг', 'devops', 'https', 'excel', 'tableau', 'powerbi', 'machinelearning', 'ml', 'bigdata', 'oracle', 'kibana',
                'ооп', 'pathlib', 'solid', 'json', 'pytest', 'алгоритмы', 'docker', 'git', 'архитектура', 'многопроцессорность', 'mongodb',
                'многопоточность', 'асинхронность', 'asyncio', 'декораторы', 'requests', 'fastapi', 'django', 'pandas', 'sqlalchemy',
                'clickhouse']

    data = {}
    for id in ids:
        url = f'https://api.hh.ru/vacancies/{id}'
        response = requests.get(url)
        try:
            description = response.json()['description'].lower()
        except KeyError:
            continue
        if 'python' not in description.split():
            continue
        for i in description.split():
            if i in keywords:
                if i not in data:
                    data[i] = 1
                else:
                    data[i] += 1
    return data


if __name__ == "__main__":
    print(get_request())
