"""
十字路口交通灯控制系统（有限状态机 FSM）

状态定义：
    状态1：南北绿灯，东西红灯    持续 5 秒
    状态2：南北黄灯，东西红灯    持续 2 秒
    状态3：南北红灯，东西绿灯    持续 5 秒
    状态4：南北红灯，东西黄灯    持续 2 秒

切换顺序：1 → 2 → 3 → 4 → 1 → ...（不断循环）

紧急模式：
    任何时候按下数字键 1（没有装 pynput 时：输入 1 再按回车），
    系统立刻切到「南北红灯 | 东西红灯」，倒计时结束后从状态1 重新开始。
    输入 0 表示恢复正常运行。

运行方式：
    python main.py
"""

import sys
import time
import threading

# ---------------- 可调参数 ----------------
GREEN_TIME = 5        # 绿灯持续秒数
YELLOW_TIME = 2       # 黄灯持续秒数
EMERGENCY_TIME = 2    # 紧急模式（双红灯）持续秒数

# ---------------- 状态表 ----------------
# 用字典把「状态编号」映射到「该状态的灯色和时长」
STATES = {
    1: {"name": "南北绿灯 | 东西红灯", "nb": "绿灯", "dx": "红灯", "duration": GREEN_TIME},
    2: {"name": "南北黄灯 | 东西红灯", "nb": "黄灯", "dx": "红灯", "duration": YELLOW_TIME},
    3: {"name": "南北红灯 | 东西绿灯", "nb": "红灯", "dx": "绿灯", "duration": GREEN_TIME},
    4: {"name": "南北红灯 | 东西黄灯", "nb": "红灯", "dx": "黄灯", "duration": YELLOW_TIME},
}

# ---------------- 切换规则表 ----------------
# 状态机核心：编号 -> 下一个编号（状态4 回到状态1，形成环）
NEXT_STATE = {1: 2, 2: 3, 3: 4, 4: 1}

START_STATE = 1       # 每次开机 / 紧急状态结束后的起始状态


class KeyMonitor:
    """在后台监听键盘，维护一个「是否出现紧急情况」的标志。

    - 装了 pynput：全局监听按键，按 1 立即生效（不用回车）；
    - 没装 pynput：退化为读取标准输入，输入 1 + 回车生效。
    两种情况对外都只暴露 set_emergency() / is_emergency()。
    """

    def __init__(self):
        self.emergency = False          # 紧急标志
        self._lock = threading.Lock()   # 后台线程和主线程都会读写它，加锁更稳
        self._start_listener()

    # ---- 对外接口 ----
    def set_emergency(self, value):
        with self._lock:
            self.emergency = value

    def is_emergency(self):
        with self._lock:
            return self.emergency

    # ---- 启动监听 ----
    def _start_listener(self):
        try:
            from pynput import keyboard         # 第三方库，可选
        except ImportError:
            threading.Thread(target=self._read_stdin, daemon=True).start()
            return
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.start()                  # Listener 自带后台线程

    def _on_press(self, key):
        """pynput 的回调：每按下一个键就被调用一次。"""
        try:
            char = key.char                     # 普通字符键才有 .char
        except AttributeError:
            return                              # F1、Shift 这类键直接忽略
        if char == "1":
            self.set_emergency(True)
        elif char == "0":
            self.set_emergency(False)

    def _read_stdin(self):
        """没有 pynput 时的后备方案：阻塞读取一行输入。"""
        while True:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                return
            line = line.strip()
            if line == "1":
                self.set_emergency(True)
            elif line == "0":
                self.set_emergency(False)


def change_state(state):
    """状态机核心函数：给出当前状态编号，返回下一个状态编号。

    状态1 -> 状态2 -> 状态3 -> 状态4 -> 状态1 ...
    """
    return NEXT_STATE[state]


def show_state(state):
    """打印当前状态的灯色。"""
    print(f"当前状态：{STATES[state]['name']}")


def countdown(seconds, monitor):
    """倒计时打印，每秒检查一次紧急标志。

    正常走完返回 True；中途检测到紧急情况立即返回 False。
    """
    for remaining in range(seconds, 0, -1):
        print(f"剩余时间：{remaining}秒")
        time.sleep(1)
        if monitor.is_emergency():
            return False
    return True


def run_one_state(state, monitor):
    """执行一个完整状态：显示 → 倒计时 → 切换。

    返回下一个状态编号；若倒计时被紧急情况打断，返回 None。
    """
    show_state(state)
    if not countdown(STATES[state]["duration"], monitor):
        return None                     # 被紧急情况打断，交给主循环处理
    print("切换交通灯...")
    return change_state(state)


def run_emergency(monitor):
    """紧急模式：南北、东西同时红灯，持续 EMERGENCY_TIME 秒后结束。"""
    monitor.set_emergency(False)        # 先清掉触发本次紧急的按键
    print("！！！检测到紧急情况！！！")
    print("南北：红灯")
    print("东西：红灯")
    print("交通灯系统进入紧急模式")
    for remaining in range(EMERGENCY_TIME, 0, -1):
        print(f"剩余时间：{remaining}秒")
        time.sleep(1)
    monitor.set_emergency(False)        # 紧急期间又按了 1 也不会残留
    print("紧急状态结束，重新从状态1开始运行")
    print()


def main():
    """主控制流程：一个 while 循环 + 状态变量，构成状态机。"""
    print("=== 十字路口交通灯系统 ===")
    print("（按 1 进入紧急模式，按 0 恢复正常运行）")
    print()

    monitor = KeyMonitor()      # 启动后台键盘监听
    state = START_STATE         # 状态变量：整个系统当前处于哪个状态

    try:
        while True:             # 状态机不停运转
            next_state = run_one_state(state, monitor)
            if next_state is None:          # 被打断 -> 进入紧急模式
                run_emergency(monitor)
                state = START_STATE         # 紧急结束，从状态1 重新开始
                continue
            state = next_state              # 正常切换
    except KeyboardInterrupt:               # Ctrl+C 退出
        print("\n交通灯系统已停止运行。")


if __name__ == "__main__":
    main()
