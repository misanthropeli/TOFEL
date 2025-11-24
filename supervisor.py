import os
import json
import requests
from datetime import datetime, timedelta, timezone

# --- 配置区域 ---
EXAM_DATE = datetime(2026, 2, 20)
# 将此处替换为你的 GitHub 仓库链接
REPO_URL = "https://github.com/" 
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"

def get_beijing_time():
    # 强制使用 UTC 时间并加上 8 小时偏移量，确保不受服务器本地时区影响
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    return beijing_now

def get_time_info(beijing_now):
    days_left = (EXAM_DATE.date() - beijing_now.date()).days
    return days_left

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_current_task(hour, days_left, schedule):
    # 1. 检查是否进入最后冲刺期 (最后15天)
    sprint_days = schedule.get("sprint_mode_trigger_days", 15)
    if days_left <= sprint_days:
        return "🚨 考前地狱冲刺", schedule.get("sprint_message", "模考！模考！模考！")

    # 2. 获取常规日程
    routine = schedule.get("daily_routine", {})
    # 格式化小时，例如 9 点变成 "09"
    hour_str = f"{hour:02d}"
    
    # 查找任务逻辑：
    # 如果当前小时有特定任务，直接返回。
    # 如果没有（比如9点没有任务，但8点有），则寻找最近的一个“过去的任务”。
    task_info = routine.get(hour_str)
    
    if not task_info:
        # 获取所有时间点并排序 ["08", "11", "14", "17", "22"]
        sorted_keys = sorted(routine.keys())
        found_key = None
        # 倒序遍历，找到第一个小于等于当前小时的时间点
        for k in reversed(sorted_keys):
            if int(k) <= hour:
                found_key = k
                break
        
        if found_key:
            task_info = routine[found_key]

    if task_info:
        return task_info.get("task"), task_info.get("details")
    else:
        return "💤 休息/自由复习", "保持清醒，准备下一个 Time Block。"

def get_nagging_msg(hour):
    # 根据北京时间的小时数返回不同的唠叨
    if 0 <= hour < 6:
        return "熬夜伤神，快去睡觉！听力需要清醒的脑子。"
    elif 6 <= hour < 10:
        return "☀️ 早安！新的一天，从背单词开始。"
    elif 10 <= hour < 13:
        return "🍽 午饭前的时间最宝贵，别刷手机了。"
    elif 13 <= hour < 16:
        return "☕ 下午容易犯困？站起来做精听！"
    elif 16 <= hour < 20:
        return "🌇 晚饭后的黄金时间，留给口语和写作。"
    elif 20 <= hour < 24:
        return "🌙 睡前复盘，Green Grid 点亮了吗？"
    else:
        return "加油！"

def send_feishu(beijing_now, title, content, days_left):
    if not FEISHU_WEBHOOK:
        print("No Webhook found.")
        return

    # 颜色逻辑
    if days_left < 15:
        color = "carmine" 
        header_title = f"💀 仅剩 {days_left} 天 | 冲刺警报"
    elif days_left < 60:
        color = "orange"
        header_title = f"⚠️ 还有 {days_left} 天 | 紧迫感呢？"
    else:
        color = "blue"
        header_title = f"备考倒计时: {days_left} 天"

    # 获取当前时间字符串，用于调试
    time_str = beijing_now.strftime("%Y-%m-%d %H:%M")
    nagging = get_nagging_msg(beijing_now.hour)

    data = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": header_title},
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md", 
                        "content": f" **当前时间 (BJ):** {time_str}\n **赵大海:** {nagging}\n\n---\n**当前任务：{title}**\n{content}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "Chemical Engineering PhD 2027 | No Excuses."}]
                },
                {
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "✅ 去 GitHub 打卡"},
                        "url": REPO_URL,
                        "type": "primary"
                    }]
                }
            ]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=data)
        print(f"Sent notification at {time_str}")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # 1. 获取精准的北京时间
    bj_now = get_beijing_time()
    
    # 2. 计算天数
    days_left = get_time_info(bj_now)
    
    # 3. 加载计划
    schedule = load_schedule()
    
    # 4. 获取当前小时的任务
    task_title, task_details = get_current_task(bj_now.hour, days_left, schedule)
    
    # 5. 发送消息
    send_feishu(bj_now, task_title, task_details, days_left)
