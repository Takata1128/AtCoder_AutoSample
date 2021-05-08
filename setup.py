from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import os
import re
import configparser

LOGIN_URL = 'https://atcoder.jp/login?continue=https%3A%2F%2Fatcoder.jp%2F%3Flang%3Dja'
PROBLEM_INFO_LIST = ['INDEX', 'NAME', 'TL', 'ML']
TEMPLATE_FILE = './template.cc'
ABC_DIRNAME = 'ABC'
ARC_DIRNAME = 'ARC'
AGC_DIRNAME = 'AGC'
OTHER_DIRNAME = 'Others'


class TestCasesScraper:
    def __init__(self, contest_url):
        self._url = contest_url
        self.config = configparser.ConfigParser()
        self.contest_name = os.path.basename(self._url)
        self.cur_dir = os.path.dirname(__file__)
        self.cc_template = ''
        with open(TEMPLATE_FILE, mode='r') as f:
            self.cc_template = f.read()
        self._setup()

    def _setup(self):
        if 'contests/abc' in self._url:
            self.cur_dir += '/'+ABC_DIRNAME
        elif 'contests/arc' in self._url:
            self.cur_dir += '/'+ARC_DIRNAME
        elif 'contests/agc' in self._url:
            self.cur_dir += '/'+AGC_DIRNAME
        else:
            self.cur_dir += '/'+OTHER_DIRNAME
        self.cur_dir += '/' + self.contest_name
        print(self.cur_dir)
        os.makedirs(self.cur_dir, exist_ok=True)

    def _fetch_samples(self, problem_url, problem_index, sample_dir, session):
        problem_page = session.get(problem_url)
        problem_soup = BeautifulSoup(
            problem_page.text, 'lxml').select('.lang .lang-en .part section pre')
        sample_list = []
        for i, e in enumerate(problem_soup):
            if i == 0:
                file_name = sample_dir + '/' + 'Constraints'
                source = re.sub('<.*?>', '', str(e))
                with open(file_name, mode='w') as f:
                    f.write(source)
            else:
                file_name = sample_dir + '/' + \
                    ('Input' if (i % 2 == 1) else 'Output') + str((i+1)//2)
                source = str(e).lstrip("<pre>").rstrip(
                    "</pre>").replace('\r\n', '\n')
                with open(file_name, mode='w') as f:
                    f.write(source)

    def get_testcases(self):
        session = requests.session()
        self._login(session)
        task_page = session.get(self._url+'/tasks/')
        task_page_soup = BeautifulSoup(task_page.text, 'lxml')
        problems_elms = task_page_soup.select('div table tbody tr')
        for e in problems_elms:
            problem_info = e.select('td')
            link = e.find('a')
            url = link.get('href')
            sample_dir = self.cur_dir + \
                '/samples/' + os.path.basename(url)[-1]
            with open(self.cur_dir + '/' + os.path.basename(url)[-1] + '.cc', mode='w') as f:
                f.write(self.cc_template)
            os.makedirs(sample_dir, exist_ok=True)
            # dic = zip(PROBLEM_INFO_LIST, problem_info)
            self._fetch_samples(
                urljoin(self._url+'/tasks/', link.get('href')), problem_info[0], sample_dir, session)

    def _login(self, session):
        r = session.get(LOGIN_URL)
        s = BeautifulSoup(r.text, 'lxml')
        csrf_token = s.find(attrs={'name': 'csrf_token'}).get('value')
        login_info = {
            'csrf_token':  csrf_token,
            'username': self.config['DEFAULT']['USERNAME'],
            'password': self.config['DEFAULT']['PASSWORD']
        }
        result = session.post(LOGIN_URL, data=login_info)
        result.raise_for_status()
        if result.status_code == 200:
            print('Log in!')
        else:
            print('Failed to log in...')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("contest_url", help="set contest url", type=str)
    parser.add_argument("username", help='set username', type=str)
    parser.add_argument("password", help='set password', type=str)

    args = parser.parse_args()

    ac = TestCasesScraper(args.contest_url)

    if args.username and args.password:
        ac.config['DEFAULT']['USERNAME'] = args.username
        ac.config['DEFAULT']['PASSWORD'] = args.password
        with open('config.ini', 'w') as cf:
            ac.config.write(cf)
    else:
        ac.config.read('config.ini')

    ac.get_testcases()
