import requests
import json
import re

header = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

class Encrypt:
    def __init__(self, e, m):
        self.e = e
        self.m = m

    def encrypt(self, message: str) -> str:
        mm = int(self.m, 16)
        ee = int(self.e, 16)
        crypto = self._encrypt(message.encode(), mm, ee)
        return crypto.hex()

    def _pad_for_encryption(self, message: str, target_length: int) -> bytes:
        return b'\x00'*(target_length - len(message)) + message

    def _encrypt(self, message, mm: int, ee: int) -> bytes:
        keylength = self.byte_size(mm)
        padded = self._pad_for_encryption(message, keylength)
        payload = int.from_bytes(padded, 'big', signed=False)
        encrypted = pow(payload, ee, mm)
        block = encrypted.to_bytes(keylength, 'big')
        return block

    def byte_size(self, number: int) -> int:
        if number == 0:
            return 1
        quanta, mod = divmod(number.bit_length(), 8)
        if mod:
            quanta += 1
        return quanta

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
        execution_id = re.findall(r'<[\s\n ]*input[\s\n ]*type[\s\n ]*=[\s\n ]*"hidden"[\s\n ]*name[\s\n ]*=[\s\n ]*"execution"[\s\n ]*value[\s\n ]*=[\s\n ]*"(.*?)"[\s\n ]*/>', page_text)[0]
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
