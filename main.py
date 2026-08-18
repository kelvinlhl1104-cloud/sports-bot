import os
import requests
import pandas as pd

# 1. 生成賽事數據與 Excel
data = {
    "球隊": ["阿仙奴", "曼城", "利物浦", "車路士"],
    "勝": [18, 17, 16, 14],
    "和": [4, 5, 5, 6],
    "負": [3, 3, 4, 5],
    "積分": [58, 56, 53, 48]
}

df = pd.DataFrame(data)
file_name = "sports_analysis.xlsx"
df.to_excel(file_name, index=False)

# 2. 讀取 Discord 網址並發送
webhook_url = os.environ.get("DISCORD_WEBHOOK")

if webhook_url:
    with open(file_name, "rb") as f:
        requests.post(
            webhook_url,
            data={"content": "⚽ **【雲端每日自動報表】** 最新分析 Excel 檔案已生成！"},
            files={"file": f}
        )
    print("已成功傳送至 Discord！")

