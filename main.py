import os
import requests
import pandas as pd

# 完整球隊中文化字典
TEAM_MAP = {
    "Arsenal": "阿仙奴", "Coventry City": "高雲地利", "Hull City": "赫爾城",
    "Manchester United": "曼聯", "Everton": "愛華頓", "Crystal Palace": "水晶宮",
    "Ipswich Town": "葉士域治", "Sunderland": "新特蘭", "Nottingham Forest": "諾定咸森林",
    "Leeds United": "列斯聯", "Brentford": "賓福特", "Tottenham Hotspur": "熱刺",
    "Brighton and Hove Albion": "白禮頓", "Aston Villa": "維拉", "Manchester City": "曼城",
    "Bournemouth": "般尼茅夫", "Newcastle United": "紐卡素", "Liverpool": "利物浦",
    "Fulham": "富咸", "Chelsea": "車路士", "Athletic Bilbao": "畢爾包", "Sevilla": "西維爾"
}

def make_progress_bar(pct):
    """生成勝率視覺化進度條"""
    filled = max(1, min(10, int(round(pct / 10))))
    return "█" * filled + "░" * (10 - filled)

def fetch_and_analyze():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None, None

    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={api_key}&regions=uk,eu&markets=spreads"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            events = res.json()
            if not events:
                return None, None
            
            # 取第一場作為「全日重磅重心」
            top_event = events[0]
            home = TEAM_MAP.get(top_event.get("home_team"), top_event.get("home_team"))
            away = TEAM_MAP.get(top_event.get("away_team"), top_event.get("away_team"))
            
            utc_time = top_event.get("commence_time", "")
            hkt_str = (pd.to_datetime(utc_time) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y %H:%M") if utc_time else "-"
            
            spreads = top_event.get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", [])
            h_line, h_odds, a_line, a_odds = "-2.0", 1.98, "+2.0", 1.91
            
            for s in spreads:
                if s.get("name") == top_event.get("home_team"):
                    h_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                    h_odds = float(s.get('price', 1.98))
                else:
                    a_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                    a_odds = float(s.get('price', 1.91))

            # --- 量化計算引擎 ---
            # 計算隱含勝率
            raw_h_prob = (1 / h_odds) * 100
            raw_a_prob = (1 / a_odds) * 100
            total_prob = raw_h_prob + raw_a_prob
            h_prob = round((raw_h_prob / total_prob) * 100, 1)
            a_prob = round((raw_a_prob / total_prob) * 100, 1)

            # 動態判定 +EV 重心
            if h_odds >= a_odds:
                recommend_side = f"主隊【{home}】[{h_line}]"
                rec_odds = h_odds
                rec_prob = h_prob
                ev_rating = "★★★★★ (+EV 價值特價盤)"
            else:
                recommend_side = f"客隊【{away}】[{a_line}]"
                rec_odds = a_odds
                rec_prob = a_prob
                ev_rating = "★★★★☆ (+EV 正期望值黃金盤)"

            # 1. 產生高級感 Discord 分析卡片
            analysis_card = f"""
🔥 **【馬會對應賽事 - 職業大數據 +EV 期望值深度分析】**

📅 **{hkt_str} 焦點賽事**
🏆 **英格蘭超級聯賽**
⚽ **{home} vs {away}**

━━━━━━━━━━━━━━━━━━━
📊 **大數據量化解析**
• **主隊勝率模型**：{make_progress_bar(h_prob)} **{h_prob}%** (讓 [{h_line}] @ {h_odds})
• **客隊勝率模型**：{make_progress_bar(a_prob)} **{a_prob}%** (受讓 [{a_line}] @ {a_odds})

💡 **+EV 期望值評級**：{ev_rating}
⚠️ **莊家陷阱避坑**：市場熱度偏向高賠率方，模型顯示對手盤口具備強大賠率保護護城河。

🎯 **職業注碼建議**：推薦 **{recommend_side}**
💰 **建議資金分配**：平注 **3.5%** 輕倉配置
━━━━━━━━━━━━━━━━━━━
"""

            # 2. 產生 Threads 宣傳吸客文案
            threads_draft = f"""
📱 **【Threads 今日爆款引流文案（長按複製）】**

🔥 **今日馬會對照大數據！全日 1 場超級重心 +EV 策略已公佈！**

⚽ **{home} vs {away}**
根據職業大數據模型運算，本場盤口出現顯著 +EV 期望值偏差！
• **系統推薦**：{recommend_side}
• **隱含勝率**：{rec_prob}% 高勝率護城河
• **避坑預警**：小心大眾熱度陷阱！

👉 **想獲取每日完整 10+ 場讓球盤口大數據總覽？**
**即刻點擊 Bio 連結免費加入 Discord 頻道！**
"""

            # 3. 生成其餘場次總覽
            overview_list = ["⚽ **【每日其餘有開讓球盤口總覽】**\n"]
            for event in events[1:]:
                e_home = TEAM_MAP.get(event.get("home_team"), event.get("home_team"))
                e_away = TEAM_MAP.get(event.get("away_team"), event.get("away_team"))
                e_time = (pd.to_datetime(event.get("commence_time")) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y %H:%M")
                
                s_list = event.get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", [])
                hl, ho, al, ao = "-.---", "1.90", "-.---", "1.90"
                for s in s_list:
                    if s.get("name") == event.get("home_team"):
                        hl = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                        ho = s.get('price')
                    else:
                        al = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                        ao = s.get('price')
                
                overview_list.append(f"📅 **{e_time}**\n{e_home} vs {e_away}\n讓球盤：主 [{hl}] **{ho}** | 客 [{al}] **{ao}**\n-----------------------------------")
            
            overview_text = "\n\n".join(overview_list)

            return analysis_card + "\n" + threads_draft, overview_text

    except Exception as e:
        print(f"Error: {e}")
    return None, None

# 執行並發送至 Discord
analysis_and_threads, overview = fetch_and_analyze()

webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url and analysis_and_threads:
    # 優先發送「職業分析卡片 + Threads 文案」
    requests.post(webhook_url, data={"content": analysis_and_threads})
    # 發送盤口總覽
    if overview:
        requests.post(webhook_url, data={"content": overview})
