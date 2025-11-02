import re
import db
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import *
import time
from datetime import datetime
from googletrans import Translator
import requests
from typing import Optional

#Logging debug JS
import json
import os

# Tạo thư mục logs nếu chưa có
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
# logging.basicConfig(level=logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'main_{datetime.now().strftime("%Y%m%d")}.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
with open("crawl-data.js", "r", encoding="utf-8") as file:
    JAVASCRIPT_SCRIPT = file.read()

class User:
    def __init__(self, id: str, link: str, name: str = ""):
        self.id = id
        self.link = link
        self.name = name if name else id
def save_js_logs_to_file(logs, user_id):
    """Lưu logs từ JavaScript vào file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"js_crawl_{user_id}_{timestamp}.log")
    
    try:
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(f"{'='*80}\n")
            f.write(f"JavaScript Crawl Logs - User: {user_id}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            
            for log_entry in logs:
                f.write(f"[{log_entry['timestamp']}] {log_entry['message']}\n")
                if log_entry.get('data'):
                    f.write(json.dumps(log_entry['data'], indent=2, ensure_ascii=False))
                    f.write("\n")
                f.write(f"{'-'*80}\n")
        
        logger.info(f"Saved JavaScript logs to {log_filename}")
        return log_filename
    except Exception as e:
        logger.error(f"Error saving JavaScript logs: {e}")
        return None

def get_input_links(file_path: str) -> list[str]:
    with open(file_path, "r") as file:
        return file.readlines()


def get_id_from_link(link: str) -> str | None:
    if not re.match(r"^https://www.facebook.com/\d+$", link):
        return None
    return link.split("/")[-1]


def process_link() -> list[User]:
    logger.info("Processing links")

    links = get_input_links("links.txt")
    user_list: list[User] = []
    for link in links:
        link = link.strip()
        id = get_id_from_link(link)
        if id:
            user_list.append(User(id, link))

    user_list = list(set(user_list))
    for user in user_list:
        user_from_db = db.get_user(user.id)
        if not user_from_db:
            db.add_user(user.id, user.link)
        else:
            logger.debug(
                "User %s already exists with name %s", user.id, user_from_db[2]
            )

    logger.info("Processing links done, found %d distinct users", len(user_list))
    return user_list


def open_browser() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()

    if BROWSER_HEADLESS:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("--user-agent=" + BROWSER_USER_AGENT)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--js-flags=--noexpose_wasm,--jitless")
    #Add
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     chrome_options.add_experimental_option('useAutomationExtension', False)
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#     "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
# })
    browser = webdriver.Chrome(options=chrome_options)

    logger.info("Browser opened")
    return browser


def prepare_browser() -> webdriver.Chrome:
    logger.info("Preparing browser")
    browser = open_browser()
    for _ in range(BROWSER_MAX_TAB_NUMBER):
        browser.execute_script("window.open('about:blank', '_blank');")

    logger.info("Opened %d tabs", BROWSER_MAX_TAB_NUMBER)
    logger.info("Browser prepared")
    return browser


def login_facebook(browser: webdriver.Chrome):
    logger.info("Logging in to Facebook")
    try:
        browser.get(FACEBOOK_LOGIN_URL)
        wait = WebDriverWait(browser, 1000)
        wait.until(EC.presence_of_element_located((By.ID, "email")))

        browser.find_element(By.ID, "email").send_keys(FACEBOOK_EMAIL)
        browser.find_element(By.ID, "pass").send_keys(FACEBOOK_PASSWORD)
        browser.find_element(By.ID, "loginbutton").click()

        wait.until(EC.title_is(f"Facebook"))
        time.sleep(4)
        logger.info("Logged in to Facebook")
        # browser.close()
        # browser.get("https://facebook.com")
    except Exception as e:
        logger.error("Error logging in to Facebook: %s", e)
        raise e


def segment_user_list(user_lists: list[User], max_tab_number: int) -> list[list[User]]:
    return [
        user_lists[i : i + max_tab_number]
        for i in range(0, len(user_lists), max_tab_number)
    ]


TELEGRAM_BOT_TOKEN = "7969047209:AAGxoF-JI71g6rtwS4mTaEeXRSSeDflXmB4"  
TELEGRAM_CHAT_ID = "7944860105"  



def translate_to_vietnamese(text):
        try:
            translator = Translator()
            # Dịch văn bản sang tiếng Việt
            translated = translator.translate(text, dest='vi')
            return translated.text
        except Exception as e:
            return f"Lỗi khi dịch: {str(e)}"
        
def send_to_telegram(post_id, link, user_id, name, content, timestamp):
    """Gửi bài đăng đến Telegram với định dạng đẹp (MarkdownV2)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    
    name = name or "Không xác định"
    content = content or "Không có nội dung"
    timestamp = timestamp or "Không rõ thời gian"
    content_short = ' '.join(content.split()[:50])
    if len(content.split()) > 50:
        content_short += "..."

    
    def escape_markdown(text):
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

    
    message = (
        f"👤 *Người đăng:* {escape_markdown(name)}\n"
        f"📝 *Nội dung:*\n`{translate_to_vietnamese(escape_markdown(content_short))}`\n"
        f"🔗 [Xem chi tiết tại đây]({link})"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "MarkdownV2",  # Sử dụng MarkdownV2 để có nhiều tùy chọn định dạng
        "disable_web_page_preview": False  # Tắt xem trước link để tin nhắn gọn hơn
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Telegram API error: {response.text}")
        logger.info(f"Đã gửi bài đăng {post_id} đến Telegram")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi gửi bài đăng {post_id}: {str(e)}")
        return False
# def parse_user_profile(browser: webdriver.Chrome, user: User):
#     user_data = db.get_user(user.id)
#     if not user_data:
#         logger.error("User %s not found in db", user.name)
#         return
#     renamed = False
#     logger.info("Parsing user profile %s", user.id)
#     links = browser.execute_script(JAVASCRIPT_SCRIPT)
#     for id, data in links.items():
#         if not db.get_post(id):
#             link = data["link"]
#             name = data["name"]
#             content = data["content"]
#             # Cant get the time from the page
#             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             logger.info("Adding post %s\t%s\t%s\t%s", id, name, content, timestamp)
#             db.add_post(
#                 id=id,
#                 link=link,
#                 user_id=user.id,
#                 name=name,
#                 content=content,
#                 timestamp=timestamp,
#             )
#             send_to_telegram(id, link, user.id, name, content, timestamp)
#         if 'name' in locals() and not user_data[2] and name and not renamed:
#             db.update_user_name(user.id, name=name)
#             logger.info("Renamed user %s to %s", user.id, name)
#             renamed = True
def parse_user_profile(browser: webdriver.Chrome, user: User):
    user_data = db.get_user(user.id)
    if not user_data:
        logger.error("User %s not found in db", user.id)
        return
    
    renamed = False
    logger.info("Parsing user profile %s", user.id)
    
    try:
        # Execute JavaScript và nhận kết quả
        result = browser.execute_script(JAVASCRIPT_SCRIPT)
        
        # Kiểm tra xem result có phải là dict với keys 'links' và 'logs' không
        if isinstance(result, dict) and 'links' in result and 'logs' in result:
            links = result['links']
            logs = result['logs']
            
            # Lưu logs vào file
            save_js_logs_to_file(logs, user.id)
            logger.info(f"Received {len(logs)} log entries from JavaScript for user {user.id}")
        else:
            # Backward compatibility: nếu chỉ trả về links
            links = result
            logger.warning("No logs received from JavaScript (old format)")
        
        # Xử lý links như cũ
        for id, data in links.items():
            if not db.get_post(id):
                link = data["link"]
                name = data["name"]
                content = data["content"]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                logger.info("Adding post %s\t%s\t%s\t%s", id, name, content[:50] if content else "", timestamp)
                
                db.add_post(
                    id=id,
                    link=link,
                    user_id=user.id,
                    name=name,
                    content=content,
                    timestamp=timestamp,
                )
                send_to_telegram(id, link, user.id, name, content, timestamp)
            
            if 'name' in locals() and not user_data[2] and name and not renamed:
                db.update_user_name(user.id, name=name)
                logger.info("Renamed user %s to %s", user.id, name)
                renamed = True
                
    except Exception as e:
        logger.error(f"Error parsing user profile {user.id}: {e}")
        
def process_link_segment(browser: webdriver.Chrome, user_list: list[User]):
    logger.info("Processing link segment for %d users", len(user_list))
    for idx, user in enumerate(user_list):
        browser.switch_to.window(browser.window_handles[idx])
        #add
        # login_facebook(browser)
        #
        browser.get(user.link)

    for idx, user in enumerate(user_list):
        browser.switch_to.window(browser.window_handles[idx])
        parse_user_profile(browser, user)
        time.sleep(10)


def get_user_list_from_db() -> list[User]:
    user_list = db.get_all_users()
    return [User(user[0], user[1], user[2]) for user in user_list]


def main():
    logger.info("Starting main")
    logger.info(f"Log files will be saved to: {os.path.abspath(LOG_DIR)}")
    db.init_db()

    browser = prepare_browser()
    login_facebook(browser)
    #giải capcha bằng tay
    # time.sleep(120)
    # browser.get("https://facebook.com")
    # time.sleep(3)

    while True:
        process_link()
        user_list = get_user_list_from_db()
        user_list_chunk = segment_user_list(user_list, BROWSER_MAX_TAB_NUMBER)
        print("user list", user_list_chunk)
        start_time = time.time()
        next_time = start_time + INTERVAL_MINUTE * 60
        for user_list in user_list_chunk:
            process_link_segment(browser, user_list)
        sleep_time = next_time - time.time()
        if sleep_time > 0:
            logger.info("Sleeping for %d seconds", sleep_time)
            time.sleep(sleep_time)
        else:
            logger.info("Sleep time is negative by %d seconds, skipping", sleep_time)


if __name__ == "__main__":
    main()
