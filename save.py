import json
import os
import re
import requests
import datetime
import time
import traceback
import pytz
from typing import List

from passport import User

header = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}


class HealthReport:
    base_url = "https://healthreport.zju.edu.cn/ncov/wap/default"
    index_url = base_url + "/index"
    save_url = base_url + "/save"

    def __init__(self, user):
        self.user = user

    def get_info(self) -> dict:
        cookies = self.user.login()
        res = self.user.session.get(self.index_url, cookies=cookies, headers=header)
        res_text = res.text.replace('\n', ' ')
        raw_new_info = re.findall(r'var\s+def\s+=\s+({.*});\s+var\s+vm', res_text)[0]
        raw_new_info_ext_1 = re.findall(r'info:\s+\$\.extend\(\{(.+)\}\s*,\s*def', res_text)[0]
        raw_new_info_ext_2 = re.findall(r'def\s*,\s*\{(.*)\}\)\s*,\s*oldInfo', res_text)[0]
        raw_old_info = re.findall(r'oldInfo: (.*),.+tipMsg', res_text)[0]
        new_info = json.loads(raw_new_info)
        new_info_ext_1 = dict(filter(lambda x: len(x) == 2,
                                     [tuple(i.replace(' ', '').replace('\'', '').split(':')) for i in
                                      raw_new_info_ext_1.split(',')]))
        new_info_ext_2 = dict(filter(lambda x: len(x) == 2,
                                     [tuple(i.replace(' ', '').replace('\'', '').split(':')) for i in
                                      raw_new_info_ext_2.split(',')]))
        new_info.update(new_info_ext_1)
        new_info.update(new_info_ext_2)
        old_info = json.loads(raw_old_info)
        if len(old_info.keys()) == 0:
            new_info['sfyxjzxgym'] = '1'
            new_info['sfbyjzrq'] = '5'
            new_info['jzxgymqk'] = '1'
            new_info['sffrqjwdg'] = '0'
            new_info['sfqtyyqjwdg'] = '0'
            new_info['sfymqjczrj'] = '0'
            for key, value in list(new_info.items()):
                if isinstance(value, str) and re.match("\[.*\]", value):
                    new_info[key + '[]'] = "0"
                    del new_info[key]
            return new_info
        else:
            old_info['created'] = new_info['created']
            old_info['uid'] = new_info['uid']
            old_info['id'] = new_info['id']
            old_info['date'] = new_info['date']
            for key, value in list(new_info.items()):
                if isinstance(value, str) and re.match("\[.*\]", value):
                    old_info[key + '[]'] = "0"
                    if key in old_info:
                        del old_info[key]
            return old_info

    def save_info(self) -> str:
        try:
            info = self.get_info()
            # print(info)
            res = self.user.session.post(self.save_url, data=info, headers=header)
            res_json = json.loads(res.text)
            if res_json['e'] == 0:
                return self.user.user_id + ' submitted successfully'
            else:
                return self.user.user_id + ' submit failed\nreason: ' + res_json['m']
        except Exception as e:
            return self.user.user_id + ' submit failed\nreason: running exception:' + e.__str__() + '\n' + traceback.format_exc()


def get_user_from_env() -> List[User]:
    users_env: str = os.environ.get('USER_JSON', None)
    if users_env:
        user_json: list = json.loads(users_env)
        return [User(u['name'], u['pass']) for u in user_json]
    else:
        return []


def push(content):
    def sct(send_key, content_body):
        data = {"title": datetime.datetime.now(pytz.timezone('Asia/Shanghai')).date().__str__() + "打卡结果",
                "desp": content_body}
        r = requests.post(f"https://sctapi.ftqq.com/{send_key}.send", data=data)
        return r.text

    def email(token, target, content_body):
        data = {"token": token,
                "title": datetime.datetime.now(pytz.timezone('Asia/Shanghai')).date().__str__() + "打卡结果",
                "text": content_body,
                "to": target}
        r = requests.post("https://email.berfen.com/api.v2/", data=data)
        return r.text

    sct_send_key: str = os.environ.get('SCT_SEND_KEY', None)
    if sct_send_key:
        print(sct(sct_send_key, content))
        print("已使用Server酱·Turbo版进行推送")
    email_target: str = os.environ.get('EMAIL', None)
    email_token: str = os.environ.get('EMAIL_TOKEN', None)
    if email_target is not None and email_token is not None:
        print(email(email_token, email_target, content))
        print("已使用邮箱推送")


if __name__ == '__main__':
    push_msg = ''
    for user in get_user_from_env():
        report = HealthReport(user)
        result = report.save_info()
        print(result)
        push_msg = push_msg + result + '\n'
        time.sleep(10)
    push(push_msg)
