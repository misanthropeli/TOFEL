import os
import json
import requests
from datetime import datetime, timedelta, timezone

# --- 配置区域 ---
EXAM_DATE = datetime(2026, 2, 20)
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK")
SCHEDULE_FILE = "daily_schedule.json"

# --- 核心功能 ---

def get_beijing_time():
    # 获取精准的北京时间 (UTC+8)
    utc_now = datetime.now(timezone.utc)
    return utc_now.astimezone(timezone(timedelta(hours=8)))

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {}
    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading JSON: {e}")
        return {}

def get_nagging_msg(hour, days_left):
    """
    监督员的灵魂：根据时间段和剩余天数生成“毒鸡汤”
    """
    # 1. 语气前缀
    if days_left < 30:
        prefix = "👹 **地狱模式**"
    else:
        prefix = "😘 **赵大海**"

    # 2. 根据时间段生成文案
    if 6 <= hour < 9:
        msg = "早安，当你还在赖床时，你的竞争对手已经背完 List 5 了。"
    elif 9 <= hour < 11:
        msg = "黄金上午，如果现在还在刷手机，你是在亲手埋葬你的 PhD Offer。"
    elif 11 <= hour < 13:
        msg = "午饭吃得太饱会变笨。听力做完了吗？错题分析了吗？"
    elif 13 <= hour < 16:
        msg = "下午容易犯困？那是借口。用冷水洗把脸，SSS 听写搞起来！"
    elif 16 <= hour < 19:
        msg = "傍晚是口语最好的练习时间。张开嘴！别做哑巴科学家！"
    elif 19 <= hour < 22:
        msg = "晚上的时间决定了你和别人的差距。再坚持一下，把今天的任务清零。"
    elif 22 <= hour < 24:
        msg = "很晚了。如果你今天任务都完成了，就去睡个好觉；如果没有，请在愧疚中入睡。"
    else: # 0点到6点
        msg = "熬夜并不能感动教授，只会让你明天的听力反应变慢。去睡觉！"
    
    return prefix, msg

def send_feishu():
    if not FEISHU_WEBHOOK:
        print("❌ Error: FEISHU_WEBHOOK not set.")
        return

    # 1. 准备数据
    bj_now = get_beijing_time()
    days_left = (EXAM_DATE.date() - bj_now.date()).days
    schedule = load_schedule()
    
    # 2. 获取任务
    hour_str = f"{bj_now.hour:02d}"
    routine = schedule.get("daily_routine", {})
    task_info = routine.get(hour_str)
    
    # 智能回溯任务逻辑
    if not task_info:
        for h in ["22", "17", "14", "11", "08"]:
            if bj_now.hour >= int(h):
                task_info = routine.get(h)
                break
    
    title = task_info.get("task", "自由复习/休息") if task_info else "自由复习"
    details = task_info.get("details", "保持专注，积少成多。") if task_info else "查看你的学习清单。"

    # 3. 获取毒舌文案 (拆分为名字和内容)
    nagging_name, nagging_text = get_nagging_msg(bj_now.hour, days_left)

    # 4. 颜色与标题逻辑
    if days_left < 15:
        color = "carmine" # 红色
        header_title = f"仅剩 {days_left} 天 | 红色警报"
    elif days_left < 60:
        color = "orange" # 橙色
        header_title = f"还有 {days_left} 天 | 保持紧迫"
    else:
        color = "blue" # 蓝色
        header_title = f"备考倒计时: {days_left} 天"

    # 5. 构建美化后的卡片
    time_str = bj_now.strftime("%Y-%m-%d %H:%M")
    
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
                        "content": f"{time_str}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        # 使用引用块 (>) 让赵大海的话更突出
                        "content": f"{nagging_name} 说：\n> {nagging_text}"
                    }
                },
                {
                    "tag": "hr" # 分割线
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md", 
                        # 任务标题加粗，具体内容换行显示
                        "content": f"**📋 当前任务：{title}**\n{details}"
                    }
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "🎯 Goal: Chemical Engineering PhD 2027"}]
                }
            ]
        }
    }
    
    try:
        requests.post(FEISHU_WEBHOOK, json=data)
        print("✅ Feishu notification sent (Beautified).")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    send_feishu()
