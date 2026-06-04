import time
import random
import requests
import subprocess

from selenium import webdriver
from selenium.webdriver.common.by import By

# ================= GUI HOOKS =================
log = None
stats_labels = None
webhook_entry = None
auto_refresh_var = None
refresh_interval_entry = None
is_running = None
set_status = None          # <-- GUI status setter (color + text)
update_graph = None        # <-- graph updater (encounters)

def set_gui_refs(l, stats, webhook, auto_refresh, refresh_entry, running_func, status_setter):
    global log, stats_labels, webhook_entry, auto_refresh_var, refresh_interval_entry, is_running, set_status
    log = l
    stats_labels = stats
    webhook_entry = webhook
    auto_refresh_var = auto_refresh
    refresh_interval_entry = refresh_entry
    is_running = running_func
    set_status = status_setter

# ================= GLOBALS =================
driver = None
last_sig = None
last_time = 0
COOLDOWN = 5
last_refresh = time.time()

stats = {"encounters": 0, "attempts": 0, "rare": 0, "last": "-"}

MAP_URL = "https://delugerpg.com/map"

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

# ================= AUTO START BRAVE =================
def start_brave():
    try:
        subprocess.Popen([
            BRAVE_PATH,
            "--remote-debugging-port=9222",
           "--user-data-dir=C:\\Users\\micha\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data"
           "--profile-directory=Default"
        ])
        log("🚀 Brave launched (debug mode)")
        time.sleep(3)
    except Exception as e:
        log(f"❌ Brave launch failed: {e}")

# ================= DRIVER =================
def init_driver():
    global driver

    start_brave()

    options = webdriver.ChromeOptions()
    options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    options.debugger_address = "127.0.0.1:9222"

    # small stealth flags (don’t overdo)
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    # hide webdriver flag
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except:
        pass

    log("🟢 Connected to Brave")

# ================= HELPERS =================
def update_stats():
    stats_labels["encounters"].configure(text=f"Encounters: {stats['encounters']}")
    stats_labels["attempts"].configure(text=f"Attempts: {stats['attempts']}")
    stats_labels["rare"].configure(text=f"Rare: {stats['rare']}")
    stats_labels["last"].configure(text=f"Last: {stats['last']}")

def send_webhook(msg):
    url = webhook_entry.get()
    if url:
        try:
            requests.post(url, json={"content": msg})
        except:
            log("⚠ Webhook failed")

def is_encounter():
    try:
        return "wild" in driver.find_element(By.ID, "mapcontext").text.lower()
    except:
        return False

def get_name():
    try:
        return driver.find_element(By.ID, "dexy").text.strip()
    except:
        return "Unknown"

def get_context():
    try:
        return driver.find_element(By.ID, "mapcontext").text.lower()
    except:
        return ""

def is_rare(ctx):
    return ("legendary" in ctx) or ("mythical" in ctx)

def go_map():
    try:
        driver.get(MAP_URL)
    except:
        pass

# ================= POPUP =================
def handle_popup():
    try:
        btns = driver.find_elements(By.XPATH, "//button[contains(text(),'Close') or contains(text(),'×')]")
        for b in btns:
            if b.is_displayed():
                b.click()
                log("🧹 Popup closed")
                return True
    except:
        pass
    return False

# ================= CLOUDFLARE DETECT =================
def is_cloudflare():
    try:
        body = driver.page_source.lower()
        keywords = [
            "checking your browser",
            "performance & security",
            "verify you are human",
            "security verification",
            "cloudflare"
        ]
        return any(k in body for k in keywords)
    except:
        return False

# ================= REFRESH =================
def auto_refresh():
    global last_refresh

    if not auto_refresh_var.get():
        return

    try:
        interval = int(refresh_interval_entry.get() or 10) * 60
    except:
        interval = 600

    if time.time() - last_refresh >= interval:
        if not is_encounter():
            log("🔄 Refresh")
            go_map()
            last_refresh = time.time()

# ================= CATCH =================
def auto_catch(name):
    stats["attempts"] += 1
    stats["last"] = name
    update_stats()

    log(f"🎯 {name}")
    send_webhook(f"🎯 {name}")

    for _ in range(3):
        try:
            driver.find_element(By.ID, "catchmon").click()
            time.sleep(1)

            driver.find_element(By.XPATH, "//input[@value='Start Battle']").click()
            time.sleep(1.5)

            driver.find_element(By.ID, "item-masterball").click()
            time.sleep(0.5)

            driver.find_element(By.XPATH, "//input[contains(@value,'Throw')]").click()
            time.sleep(2)

            log(f"✅ Done {name}")
            go_map()
            return
        except:
            handle_popup()
            time.sleep(1)

    log(f"❌ Failed {name}")
    go_map()

# ================= MOVE =================
def move():
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(random.choice(["w", "a", "s", "d"]))
    except:
        pass

# ================= MAIN LOOP =================
def run_bot():
    global last_sig, last_time

    init_driver()

    while True:
        if not is_running():
            time.sleep(0.2)
            continue

        try:
            # --- Cloudflare / Verification ---
            if is_cloudflare():
                if set_status:
                    set_status("🟡 Verifying (Cloudflare)...", "yellow")
                log("🛑 Verification detected! Solve manually in Brave...")

                # Wait until user passes it
                while is_cloudflare():
                    time.sleep(2)

                log("✅ Verification passed, resuming...")
                if set_status:
                    set_status("🟢 Running", "green")
                continue

            # normal flow
            handle_popup()
            auto_refresh()

            if is_encounter():
                name = get_name()
                ctx = get_context()
                sig = f"{name}-{ctx}"

                if sig == last_sig and (time.time() - last_time) < COOLDOWN:
                    time.sleep(0.2)
                    continue

                last_sig = sig
                last_time = time.time()

                stats["encounters"] += 1
                update_stats()

                if update_graph:
                    update_graph(stats["encounters"])

                if is_rare(ctx):
                    stats["rare"] += 1
                    update_stats()
                    auto_catch(name)
                else:
                    go_map()
            else:
                move()

        except Exception as e:
            log(f"⚠ {e}")
            go_map()

        # human-ish pacing
        time.sleep(random.uniform(0.3, 0.6))