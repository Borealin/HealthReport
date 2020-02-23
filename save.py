import json
import os
import re
import requests
import passport

healthService = '?service=https%3A%2F%2Fhealthreport.zju.edu.cn%2Fa_zju%2Fapi%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fhealthreport.zju.edu.cn%252Fncov%252Fwap%252Fdefault%252Frecently%26from%3Dwap'
healthUrl = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
postUrl = "https://healthreport.zju.edu.cn/ncov/wap/default/save"


def travelSaveInfo():
    return os.listdir('pass')


def cookie2str(cookieDict):
    lst = []
    for key, value in cookieDict.items():
        lst.append(key + '=' + value)
    return '; '.join(lst)


def getInfo(s, stuId):
    cookie = passport.getPass(s, stuId)
    # cookieStr = cookie2str(cookie)
    # data = {
    #     'cookie': cookieStr,
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    # }
    res = s.get(healthUrl)
    rawPage = res.text
    rawNewInfo = re.findall(r'var def = ({.*});', rawPage)[0]
    rawOldInfo = re.findall(r'oldInfo: (.*),', rawPage)[0]
    newInfo = json.loads(rawNewInfo)
    oldInfo = json.loads(rawOldInfo)
    newInfo['address'] = oldInfo['address']
    newInfo['area'] = oldInfo['area']
    newInfo['province'] = oldInfo['province']
    newInfo['city'] = oldInfo['city']
    newInfo['sfsqhzjkk'] = "1"
    newInfo['sqhzjkkys'] = "1"
    for key, value in newInfo.items():
        if isinstance(value, list):
            newInfo.pop(key)
            newInfo[key + '[]'] = value[0]
    return newInfo


def postInfo(s, stuId):
    data = getInfo(session, stuId)
    res = s.post(postUrl, data=data)
    return res


if __name__ == '__main__':
    if not os.path.exists('pass'):
        os.mkdir('pass')
    for savedId in travelSaveInfo():
        session = requests.session()
        result = postInfo(session, savedId).text
        jsonRes = json.loads(result)
        if jsonRes['e'] == 0:
            print(savedId+' submitted successfully')
        else:
            print(savedId+' submit failed')
            print('reason: '+jsonRes['m'])
