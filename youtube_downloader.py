import yt_dlp
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # for progress bar

root = tk.Tk()
root.title("YouTube Video Downloader")
root.geometry("500x350")
root.resizable(False, False)

# --- URL input ---
tk.Label(root, text="YouTube Video URL:").pack(pady=5)
url_entry = tk.Entry(root, width=60)
url_entry.pack()

# --- Save path input ---
tk.Label(root, text="Save Folder:").pack(pady=5)
path_frame = tk.Frame(root)
path_frame.pack()
path_entry = tk.Entry(path_frame, width=45)
path_entry.pack(side=tk.LEFT, padx=10)


def browse_folder():
    path = filedialog.askdirectory()
    if path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, path)


tk.Button(path_frame, text="Browse", command=browse_folder).pack(side=tk.LEFT)

# --- Status label and progress bar ---
status_label = tk.Label(root, text="", fg="green")
status_label.pack(pady=5)

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=5)

# --- Format selection ---
tk.Label(root, text="Select Resolution:").pack()
format_var = tk.StringVar(root)
format_menu = tk.OptionMenu(root, format_var, "")
format_menu.pack(pady=5)

available_formats = {}


# --- Progress hook ---
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        percent_float = 0.0
        if percent:
            try:
                percent_float = float(percent.replace('%', ''))
            except:
                pass
        progress['value'] = percent_float
        status_label.config(text=f"Downloading... {percent}")
        root.update_idletasks()
    elif d['status'] == 'finished':
        progress['value'] = 100
        status_label.config(text="Download completed!")
        root.update_idletasks()


# --- Fetch available formats ---
def fetch_formats():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Input Error", "Please enter a YouTube URL.")
        return

    def inner():
        global available_formats
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'forcejson': True,
                'simulate': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                available_formats.clear()
                choices = []
                seen_resolutions = set()

                for f in formats:
                    height = f.get('height')
                    fmt_id = f.get('format_id')
                    if f.get('ext') == 'mp4' and height and f.get('vcodec') != 'none':
                        label = f"{height}p"
                        if label not in seen_resolutions:
                            seen_resolutions.add(label)
                            available_formats[label] = fmt_id
                            choices.append(label)

                if not choices:
                    status_label.config(text="No downloadable MP4 formats found.")
                    return

                format_var.set(choices[0])
                menu = format_menu['menu']
                menu.delete(0, 'end')
                for choice in choices:
                    menu.add_command(label=choice, command=tk._setit(format_var, choice))

                status_label.config(text="Formats fetched. Choose one.")
        except Exception as e:
            status_label.config(text=f"Error fetching formats: {e}")

    threading.Thread(target=inner).start()


# --- Download video ---
def download_video():
    url = url_entry.get().strip()
    folder = path_entry.get().strip()
    fmt_key = format_var.get()

    if not url or not folder or not fmt_key:
        messagebox.showerror("Input Error", "Please fill all fields and select a resolution.")
        return
    if not os.path.isdir(folder):
        messagebox.showerror("Path Error", "Invalid folder path.")
        return

    status_label.config(text="Starting download...")
    progress['value'] = 0
    root.update_idletasks()

    options = {
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'format': available_formats.get(fmt_key),
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
    except Exception as e:
        status_label.config(text=f"Error: {e}")


def threaded_download():
    threading.Thread(target=download_video).start()


# --- Buttons ---
tk.Button(root, text="Fetch Resolutions", command=fetch_formats, bg="#2196F3", fg="white").pack(pady=5)
tk.Button(root, text="Download Video", command=threaded_download, bg="#4CAF50", fg="white").pack(pady=10)

root.mainloop()