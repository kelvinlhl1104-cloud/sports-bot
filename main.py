import os
import requests
import pandas as pd

# (保留原本的 TEAM_MAP 與抓取賠率邏輯...)
df = fetch_sports_odds_filtered()

all_matches_cards = "⚽ **【馬會對應賽事 - 每日讓球盤口總覽】**\n\n"
if df is not None:
    for idx, row in df.iterrows():
        card = f"""📅 **{row['香港開賽時間']} 賽事**
**{row['聯賽']}**
主：{row['主隊']} | 客：{row['客隊']}
讓球盤：主 [{row['主讓球盤口']}] {row['主讓球賠率']} | 客 [{row['客讓球盤口']}] {row['客讓球賠率']}
-----------------------------------"""
        all_matches_cards += card + "\n\n"

# 直接發送到 Discord Webhook
webhook_url = os.environ.get("DISCORD_WEBHOOK")
if webhook_url:
    requests.post(webhook_url, data={"content": all_matches_cards})
