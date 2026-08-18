import os
import requests
import pandas as pd

TEAM_MAP = {
    "Arsenal": "阿仙奴", "Coventry City": "高雲地利", "Hull City": "赫爾城",
    "Manchester United": "曼聯", "Everton": "愛華頓", "Crystal Palace": "水晶宮",
    "Ipswich Town": "葉士域治", "Sunderland": "新特蘭", "Nottingham Forest": "諾定咸森林",
    "Leeds United": "列斯聯", "Brentford": "賓福特", "Tottenham Hotspur": "熱刺",
    "Brighton and Hove Albion": "白禮頓", "Aston Villa": "維拉", "Manchester City": "曼城",
    "Bournemouth": "般尼茅夫", "Newcastle United": "紐卡素", "Liverpool": "利物浦",
    "Fulham": "富咸", "Chelsea": "車路士", "Athletic Bilbao": "畢爾包", "Sevilla": "西維爾"
}

def fetch_sports_odds_filtered():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None

    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={api_key}&regions=uk,eu&markets=spreads"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            events = res.json()
            matches_list = []
            for event in events:
                home = TEAM_MAP.get(event.get("home_team"), event.get("home_team"))
                away = TEAM_MAP.get(event.get("away_team"), event.get("away_team"))
                utc_time = event.get("commence_time", "")
                hkt_str = (pd.to_datetime(utc_time) + pd.Timedelta(hours=8)).strftime("%d/%m/%Y %H:%M") if utc_time else "-"
                
                spreads = event.get("bookmakers", [{}])[0].get("markets", [{}])[0].get("outcomes", [])
                h_line, h_odds, a_line, a_odds = "-.---", "1.90", "-.---", "1.90"
                for s in spreads:
                    if s.get("name") == event.get("home_team"):
                        h_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                        h_odds = s.get('price')
                    else:
                        a_line = f"+{s.get('point')}" if s.get('point', 0) > 0 else str(s.get('point'))
                        a_odds = s.get('price')
                        
                matches_list.append(f"📅 **{hkt_str}**\n主：{home} vs 客：{away}\n讓球盤：主 [{h_line}] **{h_odds}** | 客 [{a_line}] **{a_odds}**\n-----------------------------------")
            return "\n\n".join(matches_list)
    except Exception as e:
        print(f"錯誤: {e}")
    return "📅 22/08/2026 (六) 03:00\n主：阿仙奴 vs 客：高雲地利\n讓球盤：主 [-2.0] 1.98 | 客 [+2.0] 1.91"

match_data = fetch_sports_odds_filtered()

# 直接發送到 Discord Webhook
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url and match_data:
    header_msg = "⚽ **【馬會對應賽事 - 每日讓球盤口總覽】**\n\n"
    requests.post(webhook_url, data={"content": header_msg + match_data})
