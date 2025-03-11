import requests
from openai import OpenAI
from decouple import config


# MESSAGE = ()
RESUME_ID = config('RESUME_ID')
access_token = config('access_token')
refresh_token = config('refresh_token')

DEEPSEEK_API_KEY = config("DEEPSEEK_API_KEY")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


# Изменение пары access_token и refresh_token после сгорания 
def update_env_file(key, new_value):
    file_path='/Users/turov/Dev/hh/.env'
    with open(file_path, 'r') as file:
        lines = file.readlines()
    with open(file_path, 'w') as file:
        for line in lines:
            if line.startswith(key):
                file.write(f"{key}={new_value}\n")
            else:
                file.write(line)


class TokenManager:
    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token


    def refresh_access_token(self):
        url = 'https://hh.ru/oauth/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        response = requests.post(url, data=data)
        tokens = response.json()
        print(tokens)
        update_env_file('access_token', tokens['ilya_access_token'])
        update_env_file('refresh_token', tokens['ilya_refresh_token'])


    def get_header(self):
        return {'Authorization': f'Bearer {self.access_token}'}


# отклик на вакансию
def apply_to_vacancy(vacancy_id, token_manager):
    url = "https://api.hh.ru/negotiations"
    headers = token_manager.get_header()
    headers['HH-User-Agent'] = config('USER_AGENT')
    data = {
        'resume_id': RESUME_ID,
        'vacancy_id': vacancy_id,
    }
    # files = {
    #     'message': (None, MESSAGE)
    # }
    response = requests.post(url, headers=headers, data=data) #, files=files)
    if response.status_code != 201:
        print(response.status_code, response.text)


# получить подходящие вакансии и отправить отклик
def get_suitable_vacancies(token_manager):
    page = 0
    more_pages = True

    salary = 600000000
    currency = 'RUR'
    only_with_salary = 'false'
    professional_role = '121'

    i = 0
    while more_pages:
        url = f'https://api.hh.ru/resumes/{RESUME_ID}/similar_vacancies?page={page}&only_with_salary={only_with_salary}&salary={salary}\
            &currency={currency}&professional_role={professional_role}&schedule=remote&experience=noExperience&experience=between1And3'
        headers = token_manager.get_header()
        response = requests.get(url, headers=headers)

        if response.status_code == 403:
            print('# Сгорел токен, рефреш')
            token_manager.refresh_access_token()
            continue

        vacancy_data = response.json()
        for vacancy in vacancy_data['items']:
            requirement = vacancy['snippet']['requirement'] + vacancy['snippet']['responsibility']
            url = f"https://api.hh.ru/vacancies/{vacancy['id']}"
            response = requests.get(url)
            if vacancy['has_test']:
                continue
            if vacancy['archived']:
                continue
            if vacancy['response_letter_required'] is True:
                continue
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": 'Я ищу работу техническим специалистом. Это техническая должность, и это НЕ ДОЛЖЕН быть call-центр.\
Общение с клиентами допускается, если оно на техническую тему (баги, ошибки, техническая консультация по api и прочее).\
Проанализируй эту вакансию и ответь одним словом "Да" или "Нет". Эта вакансия мне подходит?'},
                    {"role": "user", "content": requirement},
                ],
                stream=False
            )

            is_vacancy_relevant = response.choices[0].message.content
            print(f'{is_vacancy_relevant} | {vacancy["id"]} | {requirement}')

            if is_vacancy_relevant in ['Нет', 'Нет.']:
                continue

            apply_to_vacancy(vacancy['id'], token_manager)
            i += 1
            print(f'Отправлено откликов: {i}')
        if i >= 5:
            break

        page += 1
        more_pages = page < vacancy_data['pages']


if __name__ == "__main__":
    token_manager = TokenManager(access_token, refresh_token)
    get_suitable_vacancies(token_manager)
