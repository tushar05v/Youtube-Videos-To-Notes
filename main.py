from tkinter import filedialog, messagebox, Frame, BOTH, X, Y
import tkinter as tk
import yt_dlp
import whisper
import os
import tempfile
import threading
from ttkbootstrap import Window, Label, Button, StringVar, Meter, Scrollbar, Scale, Radiobutton, Entry, Text, constants, Toplevel
import time
from dotenv import load_dotenv, set_key, find_dotenv
import google.generativeai as genai
from pygame import mixer


# ====================== Global Variables ======================
tooltip = None
tooltip_job = None
current_dir = None
api_key = None
api_window_main = None
question_window_main = None
api_entry = None
is_playing = False
current_position = 0
audio_length = 0
update_slider = True
manual_seek = False

# ================================ ALL Function Definitions ================================

def adjust_height(event=None):
    # Get the number of lines in the text widget
    lines = int(audio_title.index('end-1c').split('.')[0])
    
    # Set the height of the text widget to the number of lines
    audio_title.config(height=lines)

# ====================== Audio Player Functions ======================
def init_audio_player():
    mixer.init()

def load_audio(file_path):
    global audio_length, current_position
    mixer.music.load(file_path)
    audio_length = mixer.Sound(file_path).get_length()
    current_position = 0  # Reset position when loading new audio
    slider.config(to=audio_length)
    slider.set(0)
    update_time_display(0)

def toggle_play_pause():
    global is_playing
    if not is_playing:
        mixer.music.unpause() if mixer.music.get_busy() else mixer.music.play()
        play_btn.config(text="⏸")
        is_playing = True
        update_slider_position()
    else:
        mixer.music.pause()
        play_btn.config(text="▶")
        is_playing = False

def seek_audio(seconds):
    global current_position, manual_seek
    manual_seek = True
    
    if mixer.music.get_busy():  # Only seek if music is playing
        current_position = mixer.music.get_pos() / 1000 + seconds
    else:
        current_position += seconds
        
    current_position = max(0, min(current_position, audio_length))
    
    # Only set position if music is loaded
    if mixer.music.get_busy():
        mixer.music.set_pos(current_position)
        
    slider.set(current_position)
    update_time_display(current_position)
    manual_seek = False

def update_slider_position():
    if is_playing and not manual_seek:
        current_pos = mixer.music.get_pos() / 1000
        if current_pos < audio_length - 1:  # Prevent end-of-file glitch
            current_position = current_pos
            slider.set(current_pos)
            update_time_display(current_pos)
    app.after(1000, update_slider_position)

def update_time_display(position):
    mins, secs = divmod(int(position), 60)
    total_mins, total_secs = divmod(int(audio_length), 60)
    time_label.config(text=f"{mins:02d}:{secs:02d} / {total_mins:02d}:{total_secs:02d}")

def on_slider_press(event):
    global manual_seek
    manual_seek = True

def on_slider_release(event):
    global current_position, manual_seek
    current_position = slider.get()
    
    # Only set position if music is playing
    if mixer.music.get_busy():
        mixer.music.set_pos(current_position)
        
    update_time_display(current_position)
    manual_seek = False

# ------------------ Audio Saving / Directory Management ------------------
def change_dir(save_audio):
    global current_dir
    current_dir = save_audio
    question_window_main.destroy()
    start_download()

def save_audio_or_not():
    global question_window_main
    try:
        question_window_main.destroy()
    except:
        pass

    question_window_main = Frame(app, height=150, width=400, borderwidth=2, relief="ridge")
    question_window_main.place(anchor="center", relx=0.5, rely=0.5)
    question_window = Frame(question_window_main)
    question_window.place(anchor="n", rely=0, relx=0.5)

    warning_text = Text(question_window, wrap="word", height=3, width=50)
    warning_text.pack(pady=10)
    warning_text.insert('end', "Do you want to save audio?\nUnsaved audio will be deleted after transcription.")
    warning_text.tag_configure("center", justify="center")
    warning_text.tag_add("center", "1.0", "end")
    warning_text.configure(state='disabled')

    w_btn_frame = Frame(question_window)
    w_btn_frame.pack()
    Button(w_btn_frame, text="Save", command=lambda: change_dir(True)).pack(side="left", padx=2)
    Button(w_btn_frame, text="Don't Save", command=lambda: change_dir(False)).pack(padx=2)

# ------------------ Tooltip Functions ------------------
def show_tooltip(widget, message):
    global tooltip
    if tooltip:
        return

    tooltip = Toplevel(app)
    tooltip.wm_overrideredirect(True)
    tooltip.attributes("-topmost", True)

    label = tk.Label(tooltip, text=message, highlightthickness=0.5, highlightbackground="gray")
    label.pack()

    x = widget.winfo_rootx() + 20
    y = widget.winfo_rooty() + 30
    tooltip.wm_geometry(f"+{x}+{y}")

    app.after(3500, cancel_tooltip)

def schedule_tooltip(event, message):
    widget = event.widget
    if widget["state"] == "disabled":
        message = "You Didn't Save API So It's Disabled"

    global tooltip_job
    tooltip_job = app.after(3000, lambda: show_tooltip(widget, message))

def cancel_tooltip(event=None):
    global tooltip_job, tooltip
    if tooltip_job:
        app.after_cancel(tooltip_job)
        tooltip_job = None
    if tooltip:
        tooltip.destroy()
        tooltip = None


# ------------------ API Key Handling ------------------
def save_api_keys(api_key):
    """
    Saves or updates the API_KEY in the .env file.
    """
    env_path = find_dotenv() or ".env"  # Locate existing .env or create one
    
    set_key(env_path, "API_KEY", api_key)  # Update or add API_KEY
    
    messagebox.showinfo("Success", "API key saved successfully!")
    
    load_api_keys()
    d_and_t.configure(state="normal")
    api_window_main.destroy()

def load_api_keys():
    global api_key
    if not os.path.exists(".env"):
        create_api_window()
    else:
        load_dotenv()
        api_key = os.getenv("API_KEY")

def create_api_window(update_btn = False):
    global api_window_main, api_entry
    api_window_main = Frame(app, height=200, width=400, borderwidth=2, relief="ridge")
    api_window_main.place(anchor="center", relx=0.5, rely=0.5)
    app.update_idletasks()
    d_and_t.configure(state="disabled")
    api_window_main.lift()

    api_window = Frame(api_window_main, height=api_window_main.winfo_height(), width=api_window_main.winfo_width())
    api_window.place(anchor="n", rely=0, relx=0.5)

    Label(api_window, text="Enter API Key:").pack(pady=5)
    api_entry = Entry(api_window, width=50)
    api_entry.pack(pady=10, padx=10)
    api_btn = Frame(api_window)
    api_btn.pack(fill="x", padx=10)
    Button(api_btn, text="Save", command=lambda: save_api_keys(api_entry.get())).pack(pady=5, side="left", padx=5)
    if update_btn:
        Button(api_btn, text="Cancle", command=lambda: api_window_main.destroy()).pack(pady=5, side="left", padx=5)
        d_and_t.configure(state="normal")

# ------------------ Download and Audio Functions ------------------
def progress_hook(d):
    if d['status'] == 'downloading' and 'total_bytes' in d:
        progress = round((d['downloaded_bytes'] / d['total_bytes']) * 100, 1)
        d_loader.configure(amountused=progress)
    elif d['status'] == 'finished':
        d_loader.configure(amountused=100)

def download_audio(url):
    # Determine the destination directory.
    dire = os.getcwd() if current_dir else tempfile.gettempdir()
    
    # Choose output template based on current_dir:
    # - If current_dir is True, use the video's title as filename.
    # - Otherwise, use a fixed filename.
    if current_dir:
        # The %(title)s placeholder will be replaced by the video's title.
        outtmpl = os.path.join(dire, "%(title)s.%(ext)s")
    else:
        outtmpl = os.path.join(dire, "downloaded_audio.%(ext)s")
    
    options = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': outtmpl,
        'progress_hooks': [progress_hook]
    }
    
    # Remove the file beforehand if using the fixed name and it exists.
    if not current_dir:
        fixed_path = os.path.join(dire, "downloaded_audio.mp3")
        if os.path.exists(fixed_path):
            os.remove(fixed_path)
    
    with yt_dlp.YoutubeDL(options) as ydl:
        # This call downloads the audio and extracts metadata.
        info = ydl.extract_info(url, download=True)
        # Get the title from metadata; fallback to "downloaded_audio" if not available.
        title = info.get('title', 'downloaded_audio')

    audio_title.configure(state='normal')
    audio_title.delete("1.0", "end")
    audio_title.insert('end',title)
    audio_title.tag_configure("center", justify="center")
    audio_title.tag_add("center", "1.0", "end")
    audio_title.configure(state='disabled')

    # Construct the final file path.
    if current_dir:
        # yt-dlp sanitizes the title automatically.
        audio_path = os.path.join(dire, f"{title}.mp3")
    else:
        audio_path = os.path.join(dire, "downloaded_audio.mp3")

    load_audio(audio_path)
    print(f"Downloaded: {audio_path}")
    return audio_path

def select_audio_file():
    filedialog.askopenfilename(
        filetypes=[("Audio Files", "*.mp3;*.wav;*.m4a;*.flac;*.aac")]
    )

def start_download():
    url = link_input.get()
    if url:
        threading.Thread(target=transcribe_audio, args=(url,), daemon=True).start()

# ------------------ Transcription and Processing ------------------
def animate_subtext():
    text = "Transcribing..."
    while t_loader["subtext"] != "Done":
        for i in range(len(text) + 1):
            if t_loader["subtext"] == "Done":
                return
            t_loader.configure(subtext=text[:i])
            time.sleep(0.05)
            app.update()

def update_meter():
    i = 0
    while t_loader["subtext"] != "Done":
        t_loader.configure(amountused=i)
        i = (i + 1) % 101
        time.sleep(0.05)
        app.update()

def type_text(widget, text, index=0, delay=50):
    if index >= len(text):
        return

    # Check if the text starts with "**" and find the end of bold text
    if text[index:index+2] == "**":
        end_index = text.find("**", index + 2)  # Find closing "**"
        if end_index != -1:
            bold_text = text[index+2:end_index]  # Extract bold content
            widget.insert("end", bold_text, "bold")  # Insert with bold tag
            widget.see("end")
            widget.after(delay, type_text, widget, text, end_index + 2, delay)
            return

    # Normal text insertion
    widget.insert("end", text[index])
    widget.see("end")
    widget.after(delay, type_text, widget, text, index + 1, delay)


def gemini_update(message):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(message)
    return response.text

def transcribe_audio(url):
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    try:
        d_loader.configure(amountused=0)
        audio_path = download_audio(url)

        threading.Thread(target=animate_subtext, daemon=True).start()
        threading.Thread(target=update_meter, daemon=True).start()

        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        message = f"Clean and convert this transcription into good notes point-wise. Transcription: {result['text']}"
        transcription = gemini_update(message)

        t_loader.configure(subtext="Done", amountused=100)
        type_text(transcribe_text, transcription)
        messagebox.showinfo("Success", "Transcription completed successfully!")

        if not current_dir:
            os.remove(audio_path)
        os.system('cls')

    except Exception as e:
        messagebox.showerror("Error", str(e))

# ------------------ UI Interaction ------------------
def focus_in(event):
    input_var.set("")
    link_input.config(foreground="white")

# ====================== GUI Setup ======================
app = Window(themename='darkly')
app.geometry("700x600")

update_api_frame = Frame(app)
update_api_frame.pack(fill="x")

Button(update_api_frame, text="Update API", command=lambda: create_api_window(True))\
.pack(side="right", padx=5, pady=10)

Label(app, text="YouTube To Notes", font=('Helvetica', 28)).pack()

# URL Input Section
link_frame = Frame(app)
link_frame.pack(fill="x")

input_var = StringVar()
link_input = Entry(link_frame, textvariable=input_var, foreground="gray")
link_input.pack(fill='x', padx=10, pady=5)
link_input.insert(0, "Enter YouTube URL")
link_input.bind("<FocusIn>", focus_in)
link_input.bind("<Enter>", lambda e: schedule_tooltip(e, "Enter YouTube Link"))
link_input.bind("<Leave>", cancel_tooltip)

# Main Control Button
d_and_t = Button(app, text="Download And Transcribe", command=save_audio_or_not)
d_and_t.bind("<Enter>", lambda e: schedule_tooltip(e, "Downloads and transcribes audio"))
d_and_t.bind("<Leave>", cancel_tooltip)
d_and_t.pack()

# Progress Meters
load_and_play_frame = Frame(app)
load_and_play_frame.pack(fill="x", padx=10)

loader_frame = Frame(load_and_play_frame)
loader_frame.pack(side="left")

d_loader = Meter(loader_frame, textright="%", subtext="Downloading", amountused=0, metersize=150)
d_loader.pack(side="left")
t_loader = Meter(loader_frame, textright="%", subtext="Transcribing", amountused=0, metersize=150, showtext=False)
t_loader.pack()

# Frame for audio player controls (currently placeholders)
audio_player_frame = Frame(load_and_play_frame)
audio_player_frame.pack(expand=True, fill=BOTH)
audio_title = Text(audio_player_frame, wrap='word', height=1)
audio_title.pack(pady=(30,0), padx=10)
audio_title.insert("end","No Audio Selected")
audio_title.tag_configure("center", justify="center")
audio_title.tag_add("center", "1.0", "end")
audio_title.configure(state='disabled')
adjust_height()

controls = Frame(audio_player_frame)
controls.pack(side="bottom", fill="x")
slider = Scale(controls,from_=0, to=100)
slider.pack(fill=X, padx=10, pady=5)
slider.bind("<ButtonPress-1>", on_slider_press)
slider.bind("<ButtonRelease-1>", on_slider_release)

# Time display
time_label = Label(controls, text="00:00 / 00:00")
time_label.pack(side="right")
btn_frame = Frame(controls)
btn_frame.pack(side="left", padx=10)

Button(btn_frame, text="-10s", command=lambda: seek_audio(-10)).pack(side="left", padx=5)
play_btn = Button(btn_frame, text="▶", command=toggle_play_pause)
play_btn.pack(side="left", padx=5)
Button(btn_frame, text="+10s", command=lambda: seek_audio(10)).pack(side="left", padx=(5,10))

# Transcription Display
transcribe_view = Frame(app)
transcribe_view.pack(fill=BOTH, expand=True, padx=10, pady=10)

transcribe_label_scroll = Scrollbar(transcribe_view, orient="vertical", bootstyle="dark round")
transcribe_label_scroll.pack(side="right", fill="y")
transcribe_text = Text(transcribe_view, wrap="word", yscrollcommand=transcribe_label_scroll.set, height=10, width=80)
transcribe_text.pack(fill="both", expand=True)
transcribe_label_scroll.config(command=transcribe_text.yview)

# ====================== Initialization ======================

# Initialize audio player at startup
init_audio_player()

app.after(1000, load_api_keys())
app.mainloop()
