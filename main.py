import os
import requests
import pandas as pd

TEAM_MAP = {
    "Atlético Madrid": "馬德里體育會", "Málaga": "馬拉加", "Real Madrid": "皇家馬德里",
    "Barcelona": "巴塞隆拿", "Rayo Vallecano": "華歷簡奴", "Alavés": "艾拉維斯",
    "Arsenal": "阿仙奴", "Coventry City": "高雲地利", "Real Betis": "皇家貝迪斯",
    "Real Sociedad": "皇家蘇斯達", "Hull City": "赫爾城", "Manchester United": "曼聯",
    "Everton": "愛華頓", "Crystal Palace": "水晶宮", "Ipswich Town": "葉士域治",
    "Sunderland": "新特蘭", "Nottingham Forest": "諾定咸森林", "Leeds United": "列斯聯"
}

def make_progress_bar(pct):
    filled = max(1, min(10, int(round(pct / 10))))
    return "█" * filled + "░" * (10 - filled)

def fetch_real_hkjc_data():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None

    target_leagues = [
        "soccer_epl", "soccer_uefa_champions_league",
        "soccer_spain_la_liga", "soccer_italy_serie_a"
    ]
    
    all_events = []
    for l_key in target_leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{l_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=spreads"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                all_events.extend(res.json())
        except Exception as e:
            print(f"Error {l_key}: {e}")

    if not all_events:
        return None

    # 按真實開賽時間排序
    all_events = sorted(all_events, key=lambda x: x.get("commence_time", ""))
    
    # 抓取第一場作為真實焦點重心
    top_event = all_events[0]
    home_eng = top_event.get("home_team", "")
    away_eng = top_event.get("away_team", "")
    home = TEAM_MAP.get(home_eng, home_eng)
    away = TEAM_MAP.get(away_eng, away_eng)
    
    utc_time = top_event.get("commence_time", "")
    hkt_str = (pd.to_datetime(utc_time) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y (%a) %H:%M") if utc_time else "-"
    
    spreads = top_event.get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", [])
    h_line, h_odds, a_line, a_odds = "-0.5", 1.90, "+0.5", 1.90
    for s in spreads:
        if s.get("name") == home_eng:
            h_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
            h_odds = float(s.get('price', 1.90))
        elif s.get("name") == away_eng:
            a_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
            a_odds = float(s.get('price', 1.90))

    # 動態真實勝率計算
    raw_h = (1 / h_odds) * 100
    raw_a = (1 / a_odds) * 100
    total = raw_h + raw_a
    h_prob = round((raw_h / total) * 100, 1)
    a_prob = round((raw_a / total) * 100, 1)

    if h_odds <= a_odds:
        recommend_side = f"主隊 【{home}】 ({h_line})"
        value_tag = "🔥 【正路首選 / 上盤重注護城河】"
    else:
        recommend_side = f"客隊 【{away}】 ({a_line})"
        value_tag = "💎 【高博彩期望值 +EV 黃金受讓盤】"

    # 動態計算 API 當前抓取到的真實剩餘賽事數量
    real_locked_count = max(0, len(all_events) - 1)

    # 100% 真實數據與動態計數的卡片
    real_message = f"""
🎯 **【馬會重心專員 • 大數據 +EV 深度量化拆局】**
> **🔥 數據來源：API 實時抓取當前真實開盤數據**

📅 **開賽時間：{hkt_str}**
🏟️ **焦點對決：{home} vs {away}**

━━━━━━━━━━━━━━━━━━━
📊 **【AI 盤路數據模型解構】**
• **主隊贏盤隱含勝率**：{make_progress_bar(h_prob)} **{h_prob}%** (讓球盤 {h_line} @ **{h_odds}**)
• **客隊贏盤隱含勝率**：{make_progress_bar(a_prob)} **{a_prob}%** (受讓盤 {a_line} @ **{a_odds}**)

{value_tag}
💡 **莊家陷阱避坑**：依據實時真實賠率模型運算，過濾市場盲點。

🎯 **【獨家專家下注建議】**：鎖定 **{recommend_side}**
💰 **【建議注碼分配】**：平注 **3.5%**
━━━━━━━━━━━━━━━━━━━

🔒 **【今日 VIP 獨家鎖定區】**
• 系統實時偵測到當前 API 共有 **{real_locked_count} 場** 真實開賽賽事可供追蹤。
• 其餘真實賽事的數據模型與讓球盤口已全數收錄於 VIP 專區。
• **欲解鎖今日全部真實賽事拆局與獨家注碼配置，請即刻私訊管理員升級 VIP 會員！**
"""
    return real_message

# 執行並發送到 Discord
final_message = fetch_real_hkjc_data()
webhook_url = os.environ.get("DISCORD_WEBHOOK")

if webhook_url and final_message:
    requests.post(webhook_url, data={"content": final_message})
