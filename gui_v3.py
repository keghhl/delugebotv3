import customtkinter as ctk
import threading
import requests

from config_manager import save_config, load_config
import main_v3

# graph
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.geometry("760x760")
app.title("Deluge Bot V3")

# ================= LOG =================
def log(msg):
    log_box.insert("end", msg + "\n")
    log_box.see("end")

# ================= STATUS =================
def set_status(text, color):
    status.configure(text=text, text_color=color)

# ================= CONFIG =================
def apply_config():
    c = load_config()

    webhook_entry.delete(0, "end")
    webhook_entry.insert(0, c["webhook"])

    auto_refresh_var.set(c["auto_refresh"])

    refresh_entry.delete(0, "end")
    refresh_entry.insert(0, c["refresh_interval"])

    log("📂 Config loaded")

def save_cfg():
    save_config({
        "webhook": webhook_entry.get(),
        "auto_refresh": auto_refresh_var.get(),
        "refresh_interval": refresh_entry.get()
    })
    log("💾 Config saved")

# ================= WEBHOOK TEST =================
def test_webhook():
    url = webhook_entry.get()
    if not url:
        log("⚠ No webhook URL")
        return
    try:
        requests.post(url, json={"content": "🧪 Test from V3"})
        log("✅ Webhook test sent")
    except:
        log("❌ Webhook failed")

# ================= CONTROL =================
running = False

def start():
    global running
    running = True
    set_status("🟢 Running", "green")

def stop():
    global running
    running = False
    set_status("🔴 Stopped", "red")

def is_running():
    return running

# ================= GRAPH =================
gx, gy = [], []

def update_graph(val):
    gx.append(len(gx))
    gy.append(val)

    ax.clear()
    ax.plot(gx, gy)
    ax.set_title("Encounters Over Time")
    ax.set_xlabel("Ticks")
    ax.set_ylabel("Encounters")

    canvas.draw()

# ================= UI =================
ctk.CTkLabel(app, text="Deluge Bot V3", font=("Arial", 20)).pack(pady=6)

webhook_entry = ctk.CTkEntry(app, placeholder_text="Webhook URL")
webhook_entry.pack(fill="x", padx=10)

btns = ctk.CTkFrame(app)
btns.pack(pady=6)

ctk.CTkButton(btns, text="💾 Save", command=save_cfg).grid(row=0, column=0, padx=5)
ctk.CTkButton(btns, text="📂 Load", command=apply_config).grid(row=0, column=1, padx=5)
ctk.CTkButton(btns, text="🧪 Test Webhook", command=test_webhook).grid(row=0, column=2, padx=5)

status = ctk.CTkLabel(app, text="🔴 Stopped", text_color="red")
status.pack(pady=4)

ctrl = ctk.CTkFrame(app)
ctrl.pack(pady=6)

ctk.CTkButton(ctrl, text="Start", command=start).grid(row=0, column=0, padx=5)
ctk.CTkButton(ctrl, text="Stop", command=stop).grid(row=0, column=1, padx=5)

# stats
stats_labels = {
    "encounters": ctk.CTkLabel(app, text="Encounters: 0"),
    "attempts": ctk.CTkLabel(app, text="Attempts: 0"),
    "rare": ctk.CTkLabel(app, text="Rare: 0"),
    "last": ctk.CTkLabel(app, text="Last: -")
}
for lbl in stats_labels.values():
    lbl.pack()

# graph panel
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=app)
canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

# log
log_box = ctk.CTkTextbox(app, height=150)
log_box.pack(fill="both", expand=True, padx=10, pady=8)

# refresh controls
auto_refresh_var = ctk.BooleanVar(value=True)
refresh_frame = ctk.CTkFrame(app)
refresh_frame.pack(pady=6)

ctk.CTkCheckBox(refresh_frame, text="Auto Refresh", variable=auto_refresh_var).grid(row=0, column=0, padx=6)

refresh_entry = ctk.CTkEntry(refresh_frame, width=70)
refresh_entry.insert(0, "10")
refresh_entry.grid(row=0, column=1, padx=6)

# connect GUI → bot
main_v3.set_gui_refs(
    log,
    stats_labels,
    webhook_entry,
    auto_refresh_var,
    refresh_entry,
    is_running,
    set_status
)
main_v3.update_graph = update_graph

# start bot thread
threading.Thread(target=main_v3.run_bot, daemon=True).start()

apply_config()
app.mainloop()