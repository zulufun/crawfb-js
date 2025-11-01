import sqlite3
import requests
import json
from openai import OpenAI
import schedule
import time
import os

# Khởi tạo client OpenAI
client = OpenAI(
    api_key="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"
)

# Thông tin Viber API
AUTH_TOKEN = "54d0fbfedf76b579-a7c63312ea8a23af-fd46514b66102d70"
USER_ID = "oD/ly/8QWHPXnT4tj3qjPQ=="
CHANNEL_ID = "pa:6111661766431126905"
VIBER_URL = "https://chatapi.viber.com/pa/post"
VIBER_WEBHOOK_URL = "https://chatapi.viber.com/pa/set_webhook"
HEADERS = {
    "X-Viber-Auth-Token": AUTH_TOKEN,
    "Content-Type": "application/json"
}

def create_prompt(links_and_content):
    """Tạo chuỗi lời nhắc với các cặp link và content"""
    prompt = (
        "tóm tắt nội dung các bài đăng ngắn gọn 60 ký tự bằng tiếng Việt, trả về các dòng tương ứng):\n"
    )
    for i, (link, content) in enumerate(links_and_content, 1):
        short_content = (content or "").strip()[:60]
        prompt += f"{i}. Link: {link}\n   Nội dung: {short_content if short_content else 'Không có nội dung'}\n\n"
        print(prompt)  # Debug (có thể bỏ)
    return prompt

def summarize_content(links_and_content):
    """Tóm tắt nội dung bằng OpenAI"""
    try:
        prompt = create_prompt(links_and_content)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        response = completion.choices[0].message.content.strip()
        summaries = response.split("\n")
        return [(link, summaries[i] if i < len(summaries) else "Lỗi: Không có tóm tắt") for i, (link, _) in enumerate(links_and_content)]
    except Exception as e:
        return [(link, f"Lỗi khi tóm tắt: {str(e)}") for link, _ in links_and_content]

def send_viber_message(link, summary):
    """Gửi tin nhắn Viber với nút 🔗 chứa siêu liên kết"""
    try:
        payload = {
            "from": USER_ID,
            "type": "rich_media",
            "rich_media": {
                "Type": "rich_media",
                "ButtonsGroupColumns": 6,
                "ButtonsGroupRows": 2,
                "Buttons": [
                    {
                        "Columns": 1,
                        "Rows": 2,
                        "ActionType": "open-url",
                        "ActionBody": link,
                        "Text": "🔗Link",
                        "TextSize": "large",
                        "TextVAlign": "middle",
                        "TextHAlign": "center",
                        "BgColor": "#FF0000"
                    },
                    {
                        "Rows": 2,
                        "Columns": 5,
                        "ActionType": "none",
                        "Text": f"<b>📌 {summary}</b>",
                        "TextSize": "regular",
                        "TextVAlign": "middle",
                        "TextHAlign": "left"
                    }
                ]
            }
        }
        response = requests.post(VIBER_URL, headers=HEADERS, data=json.dumps(payload))
        response_data = response.json()
        if response_data.get("status") == 0:
            print(f"Tin nhắn gửi thành công cho: {link}")
            return True
        else:
            print(f"Lỗi khi gửi tin nhắn cho {link}: {response_data.get('status_message')}")
            return False
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gửi tin nhắn cho {link}: {str(e)}")
        return False


def fetch_and_summarize_posts(db_path="app.db"):
    """Lấy, tóm tắt và gửi tất cả bài đăng mới qua Viber dựa trên timestamp"""
    try:
        # Kết nối tới cơ sở dữ liệu
        timestamp_file = "last_timestamp.txt"
        
        # Read the last timestamp from file
        if not os.path.exists(timestamp_file):
            raise FileNotFoundError(f"{timestamp_file} does not exist.")
        
        with open(timestamp_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                raise ValueError(f"{timestamp_file} is empty.")
            last_summarized_timestamp = lines[-1].strip()

        # Kết nối tới cơ sở dữ liệu
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Truy vấn lấy tất cả bài đăng mới hơn last_summarized_timestamp
        query = """
        SELECT id, link, user_id, name, content, timestamp
        FROM posts
        WHERE timestamp > ?
        ORDER BY timestamp ASC
        """
        cursor.execute(query, (last_summarized_timestamp,))

        # Lấy tất cả bản ghi
        rows = cursor.fetchall()

        # Tạo mảng hai chiều chứa link và content
        links_and_content = [(row[1], row[4]) for row in rows]
        timestamps = [row[5] for row in rows]  # Lưu timestamp để cập nhật last_summarized_timestamp
        create_prompt(links_and_content)
        # If there are new posts, append the latest timestamp to file
        if timestamps:
            latest_timestamp = timestamps[-1]  # Get the last timestamp
            with open(timestamp_file, 'a') as f:
                f.write('\n'+latest_timestamp )
        # In kết quả và gửi qua Viber
        if links_and_content:
            print(f"Found {len(links_and_content)} new posts:")
            summaries = summarize_content(links_and_content)
            for (link, summary), timestamp in zip(summaries, timestamps):
                print(f"\nLink: {link}")
                print(f"Summary: {summary}")
                send_viber_message(link, summary)
        else:
            print("No new posts found in the database.")

        #Đóng kết nối
        cursor.close()
        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")




if __name__ == "__main__":
    while True:
        fetch_and_summarize_posts()
        print("Waiting for 1 hour before next fetch...")
        time.sleep(3600)  # Sleep 1 giờ (3600 giây)
       