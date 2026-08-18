import os
import requests
import pandas as pd

# 香港馬會官方廣東話譯名字典
TEAM_MAP = {
    "Arsenal": "阿仙奴", "Coventry City": "高雲地利", "Hull City": "赫爾城",
    "Manchester United": "曼聯", "Everton": "愛華頓", "Crystal Palace": "水晶宮",
    "Ipswich Town": "葉士域治", "Sunderland": "新特蘭", "Nottingham Forest": "諾定咸森林",
    "Leeds United": "列斯聯", "Brentford": "賓福特", "Tottenham Hotspur": "熱刺",
    "Brighton and Hove Albion": "白禮頓", "Aston Villa": "維拉", "Manchester City": "曼城",
    "Bournemouth": "般尼茅夫", "Newcastle United": "紐卡素", "Liverpool": "利物浦",
    "Fulham": "富咸", "Chelsea": "車路士", "Atlético Madrid": "馬德里體育會",
    "Málaga": "馬拉加", "Rayo Vallecano": "華歷簡奴", "Alavés": "阿拉維斯",
    "Real Betis": "皇家貝迪斯", "Real Sociedad": "皇家蘇斯達", "Athletic Bilbao": "畢爾包",
    "Sevilla": "西維爾", "Valencia": "華倫西亞", "Celta Vigo": "施達",
    "Espanyol": "愛斯賓奴", "Real Madrid": "皇家馬德里", "Villarreal": "維拉利爾",
    "Getafe": "基達菲", "Barcelona": "巴塞隆拿", "CA Osasuna": "奧沙辛拿",
    "Udinese": "烏甸尼斯", "Como": "柯謨", "Inter Milan": "國際米蘭",
    "Monza": "蒙沙", "Parma": "帕爾馬", "Cagliari": "卡利亞里", "Genoa": "熱拿亞",
    "Napoli": "拿玻里", "Juventus": "祖雲達斯", "Atalanta BC": "亞特蘭大",
    "AC Milan": "AC米蘭", "Bayern Munich": "拜仁慕尼黑", "VfB Stuttgart": "史圖加特",
    "Bayer Leverkusen": "利華古遜", "RB Leipzig": "萊比錫", "Borussia Dortmund": "多蒙特"
}

LEAGUE_MAP = {
    "EPL": "英格蘭超級聯賽",
    "La Liga - Spain": "西班牙甲組聯賽",
    "Serie A - Italy": "義大利甲組聯賽",
    "Bundesliga - Germany": "德國甲組聯賽"
}

def fetch_real_sports_odds():
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None

    leagues = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"]
    matches_list = []
    
    for league_key in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=h2h"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
                for event in events:
                    home_eng = event.get("home_team", "")
                    away_eng = event.get("away_team", "")
                    league_eng = event.get("sport_title", "")
                    utc_time = event.get("commence_time", "")
                    
                    if utc_time:
                        hkt_dt = pd.to_datetime(utc_time) + pd.Timedelta(hours=8)
                        hkt_str = hkt_dt.strftime("%Y-%m-%d %H:%M")
                        day_name = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][hkt_dt.weekday()]
                    else:
                        hkt_str, day_name = "-", "-"
                    
                    bookmakers = event.get("bookmakers", [])
                    h_odds, d_odds, a_odds = None, None, None
                    if bookmakers:
                        outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])
                        for outcome in outcomes:
                            if outcome.get("name") == home_eng:
                                h_odds = outcome.get("price")
                            elif outcome.get("name") == away_eng:
                                a_odds = outcome.get("price")
                            elif outcome.get("name") == "Draw":
                                d_odds = outcome.get("price")
                    
                    matches_list.append({
                        "聯賽": LEAGUE_MAP.get(league_eng, league_eng),
                        "星期": day_name,
                        "主隊": TEAM_MAP.get(home_eng, home_eng),
                        "客隊": TEAM_MAP.get(away_eng, away_eng),
                        "香港時間 (HKT)": hkt_str,
                        "主勝(H)": h_odds,
                        "和局(D)": d_odds,
                        "客勝(A)": a_odds
                    })
        except Exception as e:
            print(f"Error fetching {league_key}: {e}")
            
    return pd.DataFrame(matches_list) if matches_list else None

# 1. 抓取數據與生成 Excel
df = fetch_real_sports_odds()

if df is not None and not df.empty:
    df = df.sort_values(by="香港時間 (HKT)").reset_index(drop=True)
    df["球賽編號"] = df["星期"] + " " + (df.index + 1).astype(str)
    cols = ["球賽編號", "聯賽", "主隊", "客隊", "香港時間 (HKT)", "主勝(H)", "和局(D)", "客勝(A)"]
    df = df[cols]

file_name = "hkjc_daily_odds.xlsx"
df.to_excel(file_name, index=False)

# 2. 調用 Gemini API 生成 Threads 廣東話引流文案
threads_post = ""
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if gemini_api_key and df is not None:
    sample_data = df.head(8).to_string(index=False)
    prompt = f"""
    你是一位精通香港馬會足智彩 (HKJC) 大數據的 Threads 營運專家。
    以下是最新抓取的熱門足球賽事與賠率數據 (已轉換為香港廣東話譯名與香港時間 HKT)：

    {sample_data}

    請完成以下任務並寫一篇 150-200 字專屬 Threads 的高吸引力貼文：
    1. 【震撼開頭】：用「今日馬會最新對應賽事 + 大數據賠率分析已更新！」吸引球迷關注。
    2. 【焦點對決點評】：挑選 1-2 場熱門對決（附香港時間與廣東話隊名）點評賠率。
    3. 【貼地口吻】：使用香港廣東話、專業數據分析與足球 Emoji。
    4. 【強烈引流】：「想獲取每日完整 44+ 場馬會對應賽事 Excel 報表？即刻點擊 Bio 連結加入 Discord VIP 頻道！」。
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            threads_post = res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API 出錯: {e}")

# 3. 推送結果至 Discord Webhook（包含一鍵複製文案 + 賽事卡片 + Excel 檔案）
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    # 傳送 Threads 專屬文案草稿
    if threads_post:
        requests.post(webhook_url, data={"content": f"📱 **【今日 Threads 貼文草稿（長按複製）】**\n\n{threads_post}"})
    
    # 傳送賽事卡片
    cards_text = "⚽ **【馬會對應賽事大數據日報】**\n\n"
    for idx, row in df.head(5).iterrows():
        dt_str = row['香港時間 (HKT)']
        if dt_str != "-":
            dt_obj = pd.to_datetime(dt_str)
            date_formatted = dt_obj.strftime("%d/%m/%Y")
            day_char = row['球賽編號'].split()[0][-1]
            header_date = f"{date_formatted} ({day_char}) 賽事"
        else:
            header_date = "賽事預告"

        card = f"""📅 **{header_date}**
**{row['球賽編號']}，{row['聯賽']}**
主：{row['主隊']}
客：{row['客隊']}

**獨家盤口賠率：**
主勝(H) **{row['主勝(H)']}**  |  和局(D) **{row['和局(D)']}**  |  客勝(A) **{row['客勝(A)']}**
-----------------------------------"""
        cards_text += card + "\n\n"

    requests.post(webhook_url, data={"content": cards_text})

    # 上傳完整 Excel
    with open(file_name, "rb") as f:
        requests.post(webhook_url, data={"content": "⚽ **【每日完整 Excel 數據檔案】**"}, files={"file": f})
