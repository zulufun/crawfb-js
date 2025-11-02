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
import pickle
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with open("crawl-link.js", "r", encoding="utf-8") as file:
    JAVASCRIPT_SCRIPT = file.read()


class User:
    def __init__(self, id: str, link: str, name: str = ""):
        self.id = id
        self.link = link
        self.name = name if name else id


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

    browser = webdriver.Chrome(options=chrome_options)

    logger.info("Browser opened")
    return browser


def save_cookies(browser: webdriver.Chrome, filepath: str = "cookies.pkl"):
    """Lưu cookies vào file"""
    cookies = browser.get_cookies()
    with open(filepath, 'wb') as file:
        pickle.dump(cookies, file)
    logger.info("Cookies saved to %s", filepath)


def load_cookies(browser: webdriver.Chrome, filepath: str = "cookies.pkl"):
    """Load cookies từ file"""
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            cookies = pickle.load(file)
        
        # Phải vào facebook.com trước khi add cookies
        browser.get("https://www.facebook.com")
        time.sleep(2)
        
        for cookie in cookies:
            # Bỏ qua các field không cần thiết
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            browser.add_cookie(cookie)
        
        logger.info("Cookies loaded from %s", filepath)
        return True
    return False


def prepare_browser(use_saved_session: bool = True) -> webdriver.Chrome:
    """
    Chuẩn bị browser với option sử dụng session đã lưu
    
    Args:
        use_saved_session: Nếu True, sẽ thử load cookies đã lưu
    """
    logger.info("Preparing browser")
    browser = open_browser()
    
    # Nếu có cookies đã lưu và muốn dùng, load cookies
    if use_saved_session and load_cookies(browser):
        browser.get("https://www.facebook.com")
        time.sleep(3)
        
        # Kiểm tra xem đã login chưa
        if is_logged_in(browser):
            logger.info("Successfully logged in using saved session")
        else:
            logger.warning("Saved session expired, need to login again")
            login_facebook(browser)
    else:
        # Không có cookies hoặc không muốn dùng, login bình thường
        login_facebook(browser)
    
    # Mở thêm các tab
    for _ in range(BROWSER_MAX_TAB_NUMBER - 1):  # -1 vì đã có 1 tab rồi
        browser.execute_script("window.open('about:blank', '_blank');")

    logger.info("Opened %d tabs total", BROWSER_MAX_TAB_NUMBER)
    logger.info("Browser prepared")
    return browser


def is_logged_in(browser: webdriver.Chrome) -> bool:
    """Kiểm tra xem đã đăng nhập Facebook chưa"""
    try:
        # Kiểm tra xem có element đặc trưng của trang đã login không
        # Ví dụ: icon profile, menu, etc.
        browser.get("https://www.facebook.com")
        time.sleep(2)
        
        # Kiểm tra xem có form login không, nếu có = chưa login
        try:
            browser.find_element(By.ID, "email")
            return False
        except:
            # Không tìm thấy form login = đã login
            return True
    except Exception as e:
        logger.error("Error checking login status: %s", e)
        return False


def login_facebook(browser: webdriver.Chrome):
    logger.info("Logging in to Facebook")
    try:
        browser.get(FACEBOOK_LOGIN_URL)
        wait = WebDriverWait(browser, 1000)
        wait.until(EC.presence_of_element_located((By.ID, "email")))

        # browser.find_element(By.ID, "email").send_keys(FACEBOOK_EMAIL)
        browser.find_element(By.ID, "pass").send_keys(FACEBOOK_PASSWORD)
        browser.find_element(By.ID, "loginbutton").click()

        wait.until(EC.title_is(f"Facebook"))
        time.sleep(4)
        
        # Lưu cookies sau khi đăng nhập thành công
        save_cookies(browser)
        
        logger.info("Logged in to Facebook")
        
        # QUAN TRỌNG: KHÔNG đóng tab login, chỉ chuyển về trang chủ
        browser.get("https://www.facebook.com")
        
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
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False
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


def parse_user_profile(browser: webdriver.Chrome, user: User):
    user_data = db.get_user(user.id)
    if not user_data:
        logger.error("User %s not found in db", user.name)
        return
    renamed = False
    logger.info("Parsing user profile %s", user.id)
    links = browser.execute_script(JAVASCRIPT_SCRIPT)
    for id, data in links.items():
        if not db.get_post(id):
            link = data["link"]
            name = data["name"]
            content = data["content"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info("Adding post %s\t%s\t%s\t%s", id, name, content, timestamp)
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


def apply_cookies_to_tab(browser: webdriver.Chrome, tab_index: int):
    """
    Áp dụng cookies từ tab đầu tiên (tab login) sang tab khác
    
    Args:
        browser: Chrome webdriver instance
        tab_index: Index của tab cần apply cookies
    """
    # Lưu cookies từ tab đầu tiên
    browser.switch_to.window(browser.window_handles[0])
    cookies = browser.get_cookies()
    
    # Chuyển sang tab mới và apply cookies
    browser.switch_to.window(browser.window_handles[tab_index])
    browser.get("https://www.facebook.com")
    time.sleep(1)
    
    for cookie in cookies:
        try:
            browser.add_cookie(cookie)
        except Exception as e:
            logger.debug("Could not add cookie: %s", e)
    
    logger.debug("Applied cookies to tab %d", tab_index)


def process_link_segment(browser: webdriver.Chrome, user_list: list[User]):
    logger.info("Processing link segment for %d users", len(user_list))
    
    # Bước 1: Mở tất cả các user link trong các tab
    for idx, user in enumerate(user_list):
        browser.switch_to.window(browser.window_handles[idx])
        
        # Apply cookies vào tab này (từ tab 0 - tab đăng nhập)
        if idx > 0:  # Tab 0 đã có cookies rồi
            apply_cookies_to_tab(browser, idx)
        
        # Load trang user
        browser.get(user.link)
        logger.info("Loaded %s in tab %d", user.link, idx)

    # Đợi tất cả trang load
    time.sleep(5)

    # Bước 2: Parse từng trang
    for idx, user in enumerate(user_list):
        browser.switch_to.window(browser.window_handles[idx])
        parse_user_profile(browser, user)
        time.sleep(2)


def get_user_list_from_db() -> list[User]:
    user_list = db.get_all_users()
    return [User(user[0], user[1], user[2]) for user in user_list]


def main():
    logger.info("Starting main")
    db.init_db()
    
    # Prepare browser với option sử dụng saved session
    browser = prepare_browser(use_saved_session=True)
    login_facebook(browser)
    browser.get("https://www.facebook.com")
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