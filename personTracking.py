import jetson.inference
import jetson.utils
import sys
import os
import time
import requests
import RPi.GPIO as GPIO
from PCA9685 import PCA9685
from apscheduler.schedulers.blocking import BlockingScheduler #定日任务模块

# 初始化舵机
PWM = PCA9685()
PWM.setPWMFreq(50)
PAN = 90
TILT = 85


# 初始化参数
OPT = {
    'network': 'SSD-Mobilenet-v2',
    'threshold': 0.85,
    'input_URI': 'csi://0',
    'output_URI': '',
    'overlay': 'box,labels,conf'
}


# 载入 detection network
NET = jetson.inference.detectNet(OPT['network'], OPT['threshold'])


# 创建 video sources & outputs
INPUT = jetson.utils.videoSource(OPT['input_URI'])
OUTPUT = jetson.utils.videoOutput(OPT['output_URI'])


# 控制舵机运行、排查是否超出度数
def pan_run(pan, tilt):
    if pan > 180:
        pan = 180
        print("Pan Out of  Range")
    if pan < 0:
        pan = 0
        print("Pan Out of  Range")
    if tilt > 120:
        tilt = 120
        print("Tilt Out of  Range")
    if tilt < 10:
        tilt = 10
        print("Tilt Out of  Range")
    PWM.setRotationAngle(0, pan)
    PWM.setRotationAngle(1, tilt)
    return pan, tilt


# 扫描180度任务时恢复到中间位置（PAN,TILT）
def pan_reset(now_angle_pan, now_angle_tilt):
    # 回归原始位置
    if now_angle_pan != "null":
        if now_angle_pan > PAN:
            if now_angle_pan > 180:
                now_angle_pan = 180
            for i in range(now_angle_pan, PAN-1, -1):
                time.sleep(0.1)
                PWM.setRotationAngle(0, i)
        if now_angle_pan < PAN:
            if now_angle_pan < 0:
                now_angle_pan = 0
            for i in range(now_angle_pan, PAN+1, 1):
                time.sleep(0.1)
                PWM.setRotationAngle(0, i)

    if now_angle_tilt != "null":
        if now_angle_tilt > TILT:
            if now_angle_tilt > 120:
                now_angle_tilt = 120
            for i in range(now_angle_tilt, TILT-1, -1):
                PWM.setRotationAngle(1, i)
                time.sleep(0.1)
        if now_angle_tilt < TILT:
            if now_angle_tilt < 10:
                now_angle_tilt = 10
            for i in range(now_angle_tilt, TILT+1, 1):
                PWM.setRotationAngle(1, i)
                time.sleep(0.1)


# 扫描人之后恢复到上一次的位置
def person_pan_reset(now_angle_pan, now_angle_tilt,pan,tilt):
    # 回归原始位置
    if now_angle_pan != "null":
        if now_angle_pan > pan:
            if now_angle_pan > 180:
                now_angle_pan = 180
            for i in range(now_angle_pan, pan-1, -1):
                time.sleep(0.1)
                PWM.setRotationAngle(0, i)
        if now_angle_pan < pan:
            if now_angle_pan < 0:
                now_angle_pan = 0
            for i in range(now_angle_pan, pan+1, 1):
                time.sleep(0.1)
                PWM.setRotationAngle(0, i)

    if now_angle_tilt != "null":
        if now_angle_tilt > tilt:
            if now_angle_tilt > 120:
                now_angle_tilt = 120
            for i in range(now_angle_tilt, tilt-1, -1):
                PWM.setRotationAngle(1, i)
                time.sleep(0.1)
        if now_angle_tilt < tilt:
            if now_angle_tilt < 10:
                now_angle_tilt = 10
            for i in range(now_angle_tilt, tilt+1, 1):
                PWM.setRotationAngle(1, i)
                time.sleep(0.1)                


# 文字转命令
def text2order(text):
    url="http://localhost:5000/chat"
    post_data = {'type':'text','query':text,'validate':'33','uuid': '44'}
    respond = requests.post(url, data=post_data)
    if respond.status_code == 200 and respond.content != b'':
        result = respond.json()


# 每天的计划
def time_to_do(conversation):
    now = time.ctime().split(" ")[-2].split(":")
    hour,minute = int(now[0]),int(now[1])
    # 早起，穿衣服，喝奶
    if hour==8 and minute==0:
        conversation.say("蓬蓬，起床了吗？现在是早晨{}点，赶快穿好衣服喝奶啦！喝完奶好出去玩啊！".format(str(hour)))
        
    # 出去玩
    elif hour==8 and minute==30:
        conversation.say("蓬蓬，我是大象！给你放点音乐，在家里热热身，然后和姥姥出去玩吧！")
        text2order("播放本地音乐")
        time.sleep(600) # 播放10分钟音乐
        text2order("暂停")

    # 吃午饭
    elif hour==11 and minute==30:
        conversation.say("蓬蓬，我是大象！吃午饭了吗？姥姥和太太给你做什么好吃的啦？坐好乖乖吃饭，别让姥姥着急！")
    # 午睡
    elif hour==12 and minute==30:
        conversation.say("蓬蓬，我是大象！吃完饭了吧！听会音乐，要开始准备睡午觉了！让姥姥姥爷也休息一会儿吧！")
        text2order("播放本地音乐")
        time.sleep(600) # 播放10分钟音乐
        text2order("暂停")
    # 听音乐
    elif hour==15 and minute==30:
        conversation.say("蓬蓬，我是大象！睡得好吗？该起床啦，吃点水果，下午出去透透气，和别的小朋友一起玩一会儿！")
        text2order("播放本地音乐")
        time.sleep(600) # 播放10分钟音乐
        text2order("暂停")
    # 吃晚饭
    elif hour==17 and minute==0:
        conversation.say("蓬蓬，我是大象！今天玩的开心吗？现在是下午{}点，又到吃饭时间啦！要好好吃饭不挑食哦！".format(str(hour)))
    # 妈妈下班
    elif hour==19 and minute==0:
        conversation.say("蓬蓬，我是大象！现在是晚上{}点，妈妈就要下班了，高不高兴？准备跑到门口迎接妈妈吧！".format(str(hour)))
    # 听音乐
    elif hour==19 and minute==10:
        conversation.say("蓬蓬，我是大象！现在是娱乐时间，在屋子里跑跑，我给你放首歌曲怎么样？")
        text2order("播放本地音乐")
        time.sleep(600) # 播放10分钟音乐
        text2order("暂停")
    # 洗脸
    elif hour==20 and minute==10:
        conversation.say("蓬蓬，我是大象！跑的累不累？是不是出了一身汗，男子汉要不怕累，准备洗脸洗脚啦！")
    # 爸爸下班
    elif hour==20 and minute==30:
        conversation.say("蓬蓬，我是大象！爸爸就要下班回来啦！看看有没有给你带了好玩意？快来迎接爸爸！")
    # 喝奶
    elif hour==20 and minute==40:
        conversation.say("蓬蓬，我是大象！晚上是不是还没有喝奶，等着爸爸给你充奶吧！喝完奶记得刷牙哦！")
    # 看书
    elif hour==21 and minute==0:
        conversation.say("蓬蓬，我是大象！现在是晚上{}点，让爸爸给你讲一会玛德琳吧？或者让妈妈给你讲讲帐篷的故事怎么样？".format(str(hour)))
    # 睡觉
    elif hour==21 and minute==30:
        conversation.say("蓬蓬，我是大象！已经九点半啦！准备要关灯睡觉喽！")
    else:
        conversation.say("我是大象，我发现你啦！快喊我的名字叫醒我吧！")    



# 追踪人
def person_track(pan, tilt,conversation):
    start_time = time.time()
    pan_ever,tilt_ever = pan,tilt
    count = 0.0001
    while True:
        # capture the next image
        img = INPUT.Capture()
        width = INPUT.GetWidth()  # 获取视频宽度
        height = INPUT.GetHeight()  # 获取视频高度

        # detect objects in the image (with overlay)
        detections = NET.Detect(img, overlay=OPT['overlay'])
        # 找到person的detection
        detection_person_list = [x for x in detections if x.ClassID==1]
        if detection_person_list.__len__() == 1:
            confidence_max = detection_person_list[0].Confidence
        elif detection_person_list.__len__() > 1:
            confidence_max = max([x.Confidence for x in detection_person_list])
        else:
            break
        print("detected {:d} people in image".format(detection_person_list.__len__()))
        for detection in detection_person_list:
            try:
                if detection.Confidence == confidence_max:
                    start_time = time.time()  # 一旦出现人立马重置起始时间
                    # 舵机控制模块
                    objX = detection.Center[0]  # 获取矩形框的中心位置坐标
                    objY = detection.Center[1]
                    errorPan = objX - width / 2
                    errorTilt = objY - height / 2
                    if abs(errorPan) > 15:
                        pan_ever = pan_ever - errorPan / 75
                    if abs(errorTilt) > 15:
                        tilt_ever = tilt_ever + errorTilt / 75
                    pan, tilt = list(map(round,pan_run(pan_ever, tilt_ever)))
                    if count == 0.0001:
                        time_to_do(conversation)
                    break
            except Exception as e:
                print(e)

        count += 0.0001
        # render the image
        OUTPUT.Render(img)

        # update the title bar
        OUTPUT.SetStatus("{:s} | Network {:.0f} FPS".format(OPT['network'], NET.GetNetworkFPS()))

        # print out performance info
        NET.PrintProfilerTimes()

        # exit on input/output EOS
        if not INPUT.IsStreaming() or not OUTPUT.IsStreaming():
            break

        # 如果15秒内没有人出现则关闭并恢复原位置
        end_time = time.time()
        time_check = end_time - start_time
        if time_check > 15:
            break
    return pan, tilt


# 扫描180度搜索是否有人
def turn_around(conversation):
    # 扫描前半部分
    for i in range(PAN, 10, -1):
        pan, tilt = pan_run(pan=i, tilt=TILT)
        time.sleep(0.1)
        if i % 20 == 0:
            pan_person, tilt_person = person_track(pan=pan,tilt=tilt,conversation=conversation)
            person_pan_reset(now_angle_pan=pan_person,now_angle_tilt=tilt_person,pan=pan,tilt=tilt)
    if pan_person == 20 and tilt_person == tilt:
        print("上半圈未发现人，回到{}度".format(str(PAN)))
        pan_reset(now_angle_pan=i, now_angle_tilt=tilt)
    else:
        pan_reset(now_angle_pan=pan_person, now_angle_tilt=tilt_person)
    print("上半圈扫描完毕")
    time.sleep(2)

    # 扫描后半部分
    for j in range(PAN, 170, 1):
        pan, tilt = pan_run(pan=j, tilt=TILT)
        time.sleep(0.1)
        if pan % 20 == 0:
            pan_person, tilt_person = person_track(pan=pan,tilt=tilt,conversation=conversation)
            person_pan_reset(now_angle_pan=pan_person,now_angle_tilt=tilt_person,pan=pan,tilt=tilt)   
    if pan_person == 160 and tilt_person == tilt:
        print("下半圈未发现人，回到{}度".format(str(PAN)))
        pan_reset(now_angle_pan=pan, now_angle_tilt=tilt)
    else:
        pan_reset(now_angle_pan=pan_person, now_angle_tilt=tilt_person)
    print("下半圈扫描完毕")
    conversation.say("我是大象，蓬蓬你在哪啊？我找不到你！快喊我的名字叫醒我吧！")
    return False


def daily_task(conversation):
    scheduler = BlockingScheduler()
    scheduler.add_job(turn_around,'cron', hour=8,minute=0,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=8,minute=30,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=11,minute=30,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=12,minute=30,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=15,minute=30,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=17,minute=0,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=19,minute=0,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=19,minute=10,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=20,minute=0,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=20,minute=10,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=20,minute=30,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=20,minute=40,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=21,minute=0,args=[conversation])
    scheduler.add_job(turn_around,'cron', hour=21,minute=30,args=[conversation])
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass