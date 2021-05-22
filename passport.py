import requests
import json
from rsa_no_padding import Encrypt
from bs4 import BeautifulSoup

header = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}


class LoginFailedException(Exception):
    def __init__(self, err='wrong user name or password'):
        Exception.__init__(self, err)


class User:
    base_url = 'https://zjuam.zju.edu.cn/cas'
    fallback_base_url = 'http://210.32.15.40/cas'
    login_url = '/login'
    pubkey_url = '/v2/getPubKey'

    def __init__(self, user_id: str, user_pass: str, session: requests.Session = None):
        self.user_id = user_id
        self.user_pass = user_pass
        if session is None:
            self.session = requests.Session()
        else:
            self.session = session
        self.session.max_redirects = 10

    def login(self) -> dict:
        try:
            page_text = self.session.get(
                self.base_url + self.login_url, headers=header).text
        except Exception as e:
            page_text = self.session.get(
                self.fallback_base_url + self.login_url, headers=header, verify=False).text
        soup = BeautifulSoup(page_text, 'lxml')
        execution_id = soup.findAll(
            'input', attrs={'name': 'execution'})[0]['value']
        enc_user_pass = self.pass_encrypt(self.user_pass)
        form = {'username': self.user_id,
                'password': enc_user_pass,
                'authcode': '',
                'execution': execution_id,
                '_eventId': 'submit'}
        try:
            self.session.post(self.base_url + self.login_url, headers=header, data=form, allow_redirects=False)
        except Exception as e:
            self.session.post(self.fallback_base_url + self.login_url, headers=header, data=form, verify=False,
                              allow_redirects=False)
        cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
        if 'iPlanetDirectoryPro' not in cookies:
            raise LoginFailedException
        else:
            if 'route' in cookies:
                del cookies['route']
            return cookies

    def pass_encrypt(self, raw_pass: str) -> str:
        try:
            result = self.session.get(
                self.base_url + self.pubkey_url, headers=header)
        except Exception as e:
            result = self.session.get(
                self.fallback_base_url + self.pubkey_url, headers=header, verify=False)
        res_json = json.loads(result.text)
        modulus = res_json['modulus']
        exponent = res_json['exponent']
        en = Encrypt(exponent, modulus)
        encrypted = en.encrypt(raw_pass)
        return encrypted
