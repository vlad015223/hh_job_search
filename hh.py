import requests
import json
from decouple import config

# Конфигурационные данные
CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')
RESUME_ID = config('RESUME_ID')
USER_AGENT = config('USER_AGENT')
MESSAGE = ("Привет! Этот отклик сделан скриптом, который я сам написал. Поэтому я мог "
           "не пройти проверку на внимательность, которую иногда оставляют в вакансиях :)\n"
           "Я читаю все входящие сообщения и отклики, поэтому пишите, пожалуйста!)")


class TokenManager:
    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def refresh_access_token(self):
        url = 'https://api.hh.ru/token'
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = requests.post(url, data=payload)
        tokens = response.json()
        print(tokens)
        self.access_token = tokens['access_token']
        self.refresh_token = tokens['refresh_token']
        
    def get_header(self):
        return {'Authorization': f'Bearer {self.access_token}'}


def get_suitable_vacancies(token_manager):
    page = 0
    more_pages = True
    suitable_vacancies = []

    while more_pages:
        url = f'https://api.hh.ru/resumes/{RESUME_ID}/similar_vacancies?page={page}'
        headers = token_manager.get_header()
        response = requests.get(url, headers=headers)

        if response.status_code == 403:
            print('# Сгорел токен, рефреш')
            token_manager.refresh_access_token()
            continue

        vacancy_data = response.json()
        for vacancy in vacancy_data['items']:
            """
            Тут спрятаны фильтры для поиска подходящей вакансии
            """
            suitable_vacancies.append(vacancy['id'])

        page += 1
        more_pages = page < vacancy_data['pages']

    return suitable_vacancies


def apply_to_vacancy(vacancy_id, token_manager):
    url = "https://api.hh.ru/negotiations"
    headers = token_manager.get_header()
    headers['HH-User-Agent'] = USER_AGENT
    data = {
        'resume_id': RESUME_ID,
        'vacancy_id': vacancy_id,
    }
    files = {
        'message': (None, MESSAGE)
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code != 201:
        print(response.status_code, response.text)


def handle_vacancies(token_manager):
    vacancies = get_suitable_vacancies(token_manager)
    vacancies_list = []
    for i, vacancy_id in enumerate(vacancies):
        if i < 200:  # максимум 200 откликов за 24 часа
            apply_to_vacancy(vacancy_id, token_manager)
            vacancies_list.append(f'https://hh.ru/vacancy/{vacancy_id}')
            print(f'Отправлено откликов: {i + 1}')
    with open('vacancies.json', 'w') as f:
        json.dump(vacancies_list, f, indent=2)


if __name__ == "__main__":
    access_token = config('access_token')
    refresh_token = config('refresh_token')
    token_manager = TokenManager(access_token, refresh_token)
    handle_vacancies(token_manager)
