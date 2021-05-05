# ZJU Health Report Auto Submission
浙江大学每日健康打卡任务，通过使用Github Action定时任务完成，无需配置服务器
## 使用方法
### add user 
```shell
python passport.py
```
### submit report
```shell
python save.py
```

## Daily Repeat

### use crontab or time.sleep() with nohup or apscheduler or ...