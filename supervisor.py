import os
import re
import json
import random
import requests
from datetime import datetime, timezone, timedelta

# --- 基础配置 ---
EXAM_DATE = datetime(2026, 2, 20)
START_DATE = datetime(2025, 11, 23)
README_FILE = "README.md"
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"
REPO_URL = "https://github.com/misanthropeli/TOFEL" # 你的仓库地址

# --- 随机毒鸡汤库 (增加不定时的人格感) ---
QUOTES = [
    "PhD 只有录取和拒信，没有中间值。",
    "你现在的松懈，就是面试时的尴尬。",
    "TPO 刷完了吗？听力全对了吗？",
    "别看手机了，你的竞争对手正在刷题。",
    "痛苦是暂时的，GPA 和 Paper 是永恒的。",
    "想做 Chemical Engineering 的科研？先搞定英语。",
    "不要假装努力，结果不会陪你演戏。",
    "今天的单词背完了吗？"
]

def get_time_info():
    # 获取北京时间
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now + timedelta(hours=8)
    
    days_left = (EXAM_DATE.date() - beijing_now.date()).days
    total_days = (EXAM_DATE.date() - START_DATE.date()).days
    days_passed = (beijing_now.date() - START_DATE.date()).days
    
    if total_days <= 0: total_days = 1
    progress = int((days_passed / total_days) * 100)
    
    return beijing_now, days_left, max(0, min(100, progress))

def make_progress_bar(percent, length=20):
    filled_length = int(length * percent // 100)
    bar = '■' * filled_length + '□' * (length - filled_length)
    return f"[{bar}] {percent}%"

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- 获取当前时间段的任务 ---
def get_current_task(hour, schedule):
    routine = schedule.get("daily_routine", {})
    
    # 简单的模糊匹配：找最近的一个时间点
    # 比如现在是 12点，应该显示 11点的任务
    target_key = "08" # 默认早上
    min_diff = 24
    
    for key in routine.keys():
        try:
            task_hour = int(key)
            diff = hour - task_hour
            # 只找过去最近的一个时间点 (diff >= 0)
            if 0 <= diff < min_diff:
                min_diff = diff
                target_key = key
        except:
            continue
            
    task_info = routine.get(target_key, {})
    return task_info.get("task", "自主复习"), task_info.get("details", "查漏补缺")

def update_readme(today_date, days_left, progress):
    if not os.path.exists(README_FILE): return

    with open(README_FILE, "r", encoding="utf-8") as f: content = f.read()

    # 1. 更新倒计时
    pattern_days = r"(\n)(.*?)(\n\s*)"
    new_day_html = f'      <h1 style="font-size: 80px; color: #333; margin: 10px 0;">{days_left} Days</h1>'
    if re.search(pattern_days, content, re.DOTALL):
        content = re.sub(pattern_days, f"\\g<1>{new_day_html}\\g<3>", content, flags=re.DOTALL)

    # 2. 更新进度条
    pattern_prog = r"(\n)(.*?)(\n\s*)"
    progress_str = make_progress_bar(progress)
    new_prog_html = f'      <h2 style="font-family: monospace; color: #0052CC;">{progress_str}</h2>'
    if re.search(pattern_prog, content, re.DOTALL):
        content = re.sub(pattern_prog, f"\\g<1>{new_prog_html}\\g<3>", content, flags=re.DOTALL)

    # 3. 每日打卡区
    today_str = today_date.strftime("%Y-%m-%d")
    if f"📅 {today_str}" not in content:
        new_checklist = f"""### 📅 {today_str} (Today)
- [ ] **Vocab**: Memorize 100 new words + Review 150
- [ ] **Listening**: Complete 3 SSS Dictations (Error < 5 words)
- [ ] **Reading**: Analyze 5 long sentences from TPO
- [ ] **Output**: Record Speaking Task 1 (3 takes)"""
        pattern_check = r"(\n)(.*?)(\n)"
        if re.search(pattern_check, content, re.DOTALL):
            content = re.sub(pattern_check, f"\\g<1>{new_checklist}\\g<3>", content, flags=re.DOTALL)

    with open(README_FILE, "w", encoding="utf-8") as f: f.write(content)

def send_feishu(days_left, progress, task_title, task_details):
    if not FEISHU_WEBHOOK: return
    
    # 随机选一句狠话
    random_quote = random.choice(QUOTES)
    
    # 颜色逻辑
    color = "blue"
    if days_left < 30: color = "red"
    elif days_left < 60: color = "orange"

    msg = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📅 倒计时: {days_left} 天 | 进度: {progress}%"},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**💡 {random_quote}**\n\n**当前任务 ({datetime.now().hour}:00):**\n{task_title}\n> {task_details}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "✅ 去 GitHub 打卡"},
                            "url": REPO_URL, 
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=msg)
        print("Feishu sent.")
    except Exception as e:
        print(f"Feishu error: {e}")

if __name__ == "__main__":
    now, days, prog = get_time_info()
    schedule = load_schedule()
    
    # 1. 更新 README
    update_readme(now, days, prog)
    
    # 2. 获取当前应该做的任务
    t_title, t_details = get_current_task(now.hour, schedule)
    
    # 3. 发送提醒
    send_feishu(days, prog, t_title, t_details)
