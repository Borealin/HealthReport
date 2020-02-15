import os

import requests
import json
import rsaNoPadding
from bs4 import BeautifulSoup

pubUrl = "https://zjuam.zju.edu.cn/cas/v2/getPubKey"
passportUrl = "https://zjuam.zju.edu.cn/cas/login"
loginUrl = "https://zjuam.zju.edu.cn/cas/login"


def passEncrypt(s, rawPass):
    result = s.get(pubUrl)
    rawJson = json.loads(result.text)
    modulus = rawJson['modulus']
    exponent = rawJson['exponent']
    en = rsaNoPadding.Encrypt(exponent, modulus)
    encrypted = en.encrypt(rawPass)
    return encrypted


def login(s, userId, userPass):
    rawPage = s.get(passportUrl).text
    soup = BeautifulSoup(rawPage, 'lxml')
    executionId = soup.findAll('input', attrs={'name': 'execution'})[0]['value']
    userPass = passEncrypt(s, userPass)
    form = {'username': userId,
            'password': userPass,
            'authcode': '',
            'execution': executionId,
            '_eventId': 'submit'}
    result = s.post(loginUrl, data=form)
    return result


def getPass(s, filename):
    try:
        with open('pass/' + filename, "rb") as json_file:
            userPass = json_file.read().decode()
            login(s, filename, userPass)
    except IOError:
        flag = True
        print(filename, '\'s password not generated ')
        userPass = ''
        while flag:
            userPass = str(input('please input password '))
            res = login(s, filename, userPass)
            cookieList = requests.utils.dict_from_cookiejar(res.cookies)
            if len(cookieList) > 0:
                print('wrong password')
            else:
                flag = False
        with open('pass/' + filename, "wb") as json_file:
            json_file.write(userPass.encode())
    return requests.utils.dict_from_cookiejar(s.cookies)


if __name__ == '__main__':
    if not os.path.exists('pass'):
        os.mkdir('pass')
    session = requests.session()
    stuId = str(input('please input stuId you want to add '))
    print(getPass(session, stuId))
