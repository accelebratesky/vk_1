"""
状态1：南北绿灯，东西红灯
状态2：南北黄灯，东西红灯
状态3：南北红灯，东西绿灯
状态4：南北红灯，东西黄灯
"""
import time
from pynput import keyboard
nb='green'
dx='red'
state=1
jima = False
def press(key):
    global jima
    try:
        if key.char == '1':
            jima = True
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=press)
listener.start()
def deal_jingji():
    global jima, state, nb, dx

    jima = False
    print("！！！检测到紧急情况！！！")
    print("南北：红灯  东西：红灯")
    for tt in range(2, 0, -1):
        print(f"剩余时间：{tt}秒\n")
        time.sleep(1)
   
    print("紧急状态结束...\n")

    state=1
    nb='green'
    dx='red'


def change_state():
    global jima, state, nb, dx
    if (state == 1):
       print("当前状态：南北绿灯 | 东西红灯\n")
       for t in range(5, 0, -1):
           print(f"剩余时间:{t}秒\n")
           time.sleep(1)
           if jima:
              deal_jingji()
              return
       print("切换交通灯...\n")

       state=2
       nb='yellow'

    elif (state == 2):
        print("当前状态：南北黄灯 | 东西红灯\n")
        for t in range(2, 0, -1):
            print(f"剩余时间：{t}秒\n")
            time.sleep(1)
            if jima:
                deal_jingji()
                return
        print("切换交通灯...\n")
        state=3
        nb='red'
        dx='green'
    elif (state == 3):
        print("当前状态：南北红灯 | 东西绿灯\n")
        for t in range(5, 0, -1):
            print(f"剩余时间：{t}秒\n")
            time.sleep(1)
            if jima:
                deal_jingji()
                return
        print("切换交通灯...\n")
        state=4
        nb='red'
        dx='yellow'
    elif (state == 4):
        print("当前状态：南北红灯 | 东西黄灯\n")
        for t in range(2, 0, -1):
            print(f"剩余时间：{t}秒\n")
            time.sleep(1)
            if jima:
                deal_jingji()
                return
        print("切换交通灯...\n")
        state=1
        nb='green'
        dx='red'

print("======= 十字路口交通灯系统 ======\n")
while True:
    change_state()
