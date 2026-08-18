import os
import requests
import pandas as pd

def fetch_real_sports_odds():
    """使用 The Odds API 抓取熱門聯賽，並自動轉換為香港時間 (HKT)"""
    api_key = os.environ.get("ODDS_API_KEY")
    if not api_key:
        print("未設定 ODDS_API_KEY")
        return None

    # 馬會必開的熱門聯賽列表：英超(epl)、西甲(la_liga)、德甲(bundesliga)、意甲(serie_a)
    leagues = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a"]
    matches_list = []
    
    for league_key in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds/?apiKey={api_key}&regions=uk,eu&markets=h2h"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                events = res.json()
                for event in events:
                    home_team = event.get("home_team", "")
                    away_team = event.get("away_team", "")
                    
                    # 1. 抓取 UTC 時間並轉為香港時間 (HKT = UTC + 8)
                    utc_time = event.get("commence_time", "")
                    if utc_time:
                        hkt_dt = pd.to_datetime(utc_time) + pd.Timedelta(hours=8)
                        hkt_str = hkt_dt.strftime("%Y-%m-%d %H:%M (%a)")
                    else:
                        hkt_str = "-"
                    
                    # 2. 提取賠率
                    h_odds, d_odds, a_odds = None, None, None
                    bookmakers = event.get("bookmakers", [])
                    if bookmakers:
                        outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])
                        for outcome in outcomes:
                            if outcome.get("name") == home_team:
                                h_odds = outcome.get("price")
                            elif outcome.get("name") == away_team:
                                a_odds = outcome.get("price")
                            elif outcome.get("name") == "Draw":
                                d_odds = outcome.get("price")
                    
                    matches_list.append({
                        "聯賽": event.get("sport_title", "足球聯賽"),
                        "主隊 (英文)": home_team,
                        "客隊 (英文)": away_team,
                        "香港開賽時間 (HKT)": hkt_str,
                        "主勝(H)": h_odds,
                        "和局(D)": d_odds,
                        "客勝(A)": a_odds
                    })
        except Exception as e:
            print(f"抓取 {league_key} 出錯: {e}")
            
    if matches_list:
        return pd.DataFrame(matches_list)
    return None

# 1. 執行數據抓取並生成 Excel
df = fetch_real_sports_odds()

if df is None or df.empty:
    df = pd.DataFrame([{
        "聯賽": "Premier League",
        "主隊 (英文)": "Arsenal",
        "客隊 (英文)": "Chelsea",
        "香港開賽時間 (HKT)": "2026-08-22 03:00 (Sat)",
        "主勝(H)": 1.95,
        "和局(D)": 3.50,
        "客勝(A)": 3.80
    }])

file_name = "hkjc_daily_odds.xlsx"
df.to_excel(file_name, index=False)

# 2. 調用 Gemini API 生成 Threads 廣東話引流文案
gemini_api_key = os.environ.get("GEMINI_API_KEY")
threads_post = "（文案生成失敗，請檢查 GEMINI_API_KEY）"

if gemini_api_key:
    sample_data = df.head(8).to_string(index=False)
    prompt = f"""
    你是一位精通香港馬會足智彩 (HKJC) 大數據的 Threads 營運專家。
    以下是最新抓取的熱門足球賽事與賠率數據 (已轉換為香港時間 HKT)：

    {sample_data}

    請完成以下任務並寫一篇 150-200 字專屬 Threads 的高吸引力貼文：
    1. 【廣東話隊名對照】：將英文隊名翻譯為香港馬會官方廣東話譯名（例如：Arsenal -> 阿仙奴, Chelsea -> 車路士, Man Utd -> 曼聯）。
    2. 【震撼開頭】：用「今日馬會開盤賽事 + 大數據賠率分析已更新！」吸引球迷關注。
    3. 【焦點對決點評】：挑選 1-2 場熱門對決（附香港時間與廣東話隊名）點評賠率。
    4. 【貼地口吻】：使用香港廣東話、專業數據分析與足球 Emoji。
    5. 【強烈引流】：「想獲取每日完整馬會對應賽事 Excel 報表？即刻點擊 Bio 連結加入 Discord VIP 頻道！」。
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            threads_post = res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini API 出錯: {e}")

# 3. 推送結果至 Discord Webhook
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    requests.post(webhook_url, data={"content": f"📝 **【今日 Threads 引流文案草稿】**\n\n{threads_post}"})
    with open(file_name, "rb") as f:
        requests.post(
            webhook_url,
            data={"content": "⚽ **【香港馬會對應熱門賽事與即時賠率】Excel 報表已生成！**"},
            files={"file": f}
        )

