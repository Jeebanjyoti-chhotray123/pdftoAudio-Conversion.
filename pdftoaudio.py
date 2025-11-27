import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pdfplumber
import pyttsx3
import threading
import re
import pytesseract
from PIL import Image
import shutil
import os
import time
import subprocess

# --- Tesseract Setup ---
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(default_path):
        pytesseract.pytesseract.tesseract_cmd = default_path
    else:
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror(
            "Tesseract Missing",
            "Tesseract OCR is not installed or not found in PATH.\n\n"
            "Please install it from:\nhttps://github.com/UB-Mannheim/tesseract/wiki"
        )
        temp_root.destroy()

# Globals
stop_thread = False
current_text = ""
theme_mode = "light"

def extract_full_text(filepath):
    try:
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text_layer = page.extract_text() or ""
                ocr_text = ""
                if len(page_text_layer.strip()) < 50:
                    try:
                        page_img = page.to_image(resolution=300).original
                        ocr_text = pytesseract.image_to_string(page_img, lang="eng") or ""
                        ocr_text = re.sub(r'^\d+$', '', ocr_text, flags=re.MULTILINE)
                        ocr_text = re.sub(r'\n\s*\n', '\n', ocr_text)
                    except Exception as ocr_err:
                        print(f"OCR failed on page {page_num}: {ocr_err}")
                combined_page_text = page_text_layer
                if ocr_text.strip() and len(ocr_text.strip()) > len(page_text_layer.strip()):
                    combined_page_text = page_text_layer + " " + re.sub(re.escape(page_text_layer), '', ocr_text, count=1).strip()
                if combined_page_text.strip():
                    text += combined_page_text + "\n\n"
                else:
                    print(f"No text extracted from page {page_num}")
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if not text:
            messagebox.showwarning("Warning", "No text found in the entire PDF, even after OCR fallback.")
            return None
        print(f"Extracted {len(text)} characters from PDF (including captions and full content).")
        return text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read PDF: {e}")
        return None

def select_pdf():
    filepath = filedialog.askopenfilename(
        title="Select PDF File",
        filetypes=[("PDF Files", "*.pdf")]
    )
    if filepath:
        pdf_path.set(filepath)
        subtitle_box.delete(1.0, tk.END)
        subtitle_box.insert(tk.END, "Processing PDF... Please wait (extracting full text including captions).")
        root.update_idletasks()
        def run_extraction():
            global current_text
            current_text = extract_full_text(filepath)
            subtitle_box.delete(1.0, tk.END)
            if current_text:
                preview = current_text[:1500] + "...\n\n(Preview - Full text extracted: " + str(len(current_text)) + " chars, including captions)" if len(current_text) > 1500 else current_text
                subtitle_box.insert(tk.END, preview)
            else:
                subtitle_box.insert(tk.END, "Could not extract text from the PDF.")
        threading.Thread(target=run_extraction, daemon=True).start()

def stop_playback():
    global stop_thread
    stop_thread = True
    status_label.config(text="Stopping...")

def play_with_subtitles():
    global stop_thread
    if not pdf_path.get():
        messagebox.showwarning("Warning", "Please select a PDF file first!")
        return
    if not current_text:
        messagebox.showwarning("Warning", "No text to read. Extract first.")
        return
    stop_thread = False
    def speak():
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty("voices")
        selected_voice = voice_choice.get()
        if selected_voice == "Male":
            engine.setProperty("voice", voices[0].id)
        elif selected_voice == "Female" and len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
        text_to_speak = re.sub(r"\s+", " ", current_text).strip()
        sentences = re.split(r'(?<=[.!?]) +', text_to_speak)
        subtitle_box.delete(1.0, tk.END)
        for sentence in sentences:
            if stop_thread:
                break
            sentence = sentence.strip()
            if not sentence:
                continue
            words = sentence.split()
            est_duration = max(1.5, len(words) * 0.4)
            root.after(0, lambda s=sentence: subtitle_box.insert(tk.END, s + "\n\n"))
            root.after(0, lambda: subtitle_box.see(tk.END))
            engine.say(sentence)
            engine.runAndWait()
            start_time = time.time()
            while time.time() - start_time < est_duration:
                if stop_thread:
                    break
                time.sleep(0.1)
        if not stop_thread:
            messagebox.showinfo("Done", "Audiobook playback finished.")
        status_label.config(text="Ready")
        engine.stop()
    status_label.config(text="Playing...")
    threading.Thread(target=speak, daemon=True).start()

def generate_audio(text, output_path, voice_choice_str):
    try:
        text_to_speak = re.sub(r"\s+", " ", text).strip()
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        voices = engine.getProperty("voices")
        if voice_choice_str == "Male" and voices:
            engine.setProperty("voice", voices[0].id)
        elif voice_choice_str == "Female" and len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
        engine.save_to_file(text_to_speak, output_path)
        engine.runAndWait()
        engine.stop()
        if not os.path.exists(output_path):
            raise Exception("Audio file was not created.")
        if os.path.getsize(output_path) == 0:
            raise Exception("Audio file is empty.")
        return True
    except Exception as e:
        print(f"Audio generation failed: {e}")
        if 'engine' in locals():
            engine.stop()
        raise e

def merge_audio_subs_to_mkv(audio_path, srt_path, mkv_path):
    try:
        ffmpeg_path = r"D:\downloads\ffmpeg-8.0-essentials_build\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe"
        if not os.path.exists(ffmpeg_path):
            raise Exception(f"FFmpeg not found at {ffmpeg_path}. Please check the path.")

        cmd = [
            ffmpeg_path,
            "-i", audio_path,
            "-i", srt_path,
            "-c", "copy",
            "-map", "0",
            "-map", "1",
            "-y",
            mkv_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(srt_path):
            os.remove(srt_path)
        print(f"Merged MKV saved to: {mkv_path}")
        return True
    except Exception as e:
        print(f"Merge failed: {e}")
        return False

def download_audio_and_subs():
    if not current_text:
        messagebox.showwarning("Warning", "No text to save. Extract first.")
        return
    if not pdf_path.get():
        base_name = "audiobook"
    else:
        base_name = os.path.splitext(os.path.basename(pdf_path.get()))[0]
    mkv_path = filedialog.asksaveasfilename(
        defaultextension=".mkv",
        filetypes=[("MKV Video File (Audio + Subtitles)", "*.mkv"), ("All Files", "*.*")],
        initialfile=base_name + ".mkv",
        title="Save Merged Audio + Subtitles File (Synced MKV)"
    )
    if mkv_path:
        temp_dir = os.path.dirname(mkv_path) or "."
        temp_audio = os.path.join(temp_dir, "temp_audio.wav")
        temp_srt = os.path.join(temp_dir, "temp_subs.srt")
        try:
            paragraphs = re.split(r'\n\n+', current_text.strip())
            sentences = []
            for para in paragraphs:
                para_sentences = re.split(r'(?<=[.!?]) +', para)
                sentences.extend([s.strip() for s in para_sentences if s.strip()])
            with open(temp_srt, "w", encoding="utf-8") as f:
                time_cursor = 0.0
                for i, s in enumerate(sentences, 1):
                    if not s:
                        continue
                    words = s.split()
                    dur = max(1.0, len(words) * 0.4)
                    start = format_srt_time(time_cursor)
                    end = format_srt_time(time_cursor + dur)
                    f.write(f"{i}\n{start} --> {end}\n{s}\n\n")
                    time_cursor += dur
            print(f"Temporary SRT created: {temp_srt}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate subtitles: {e}")
            return
        def run_generate():
            try:
                generate_audio(current_text, temp_audio, voice_choice.get())
                merge_success = merge_audio_subs_to_mkv(temp_audio, temp_srt, mkv_path)
                if merge_success:
                    root.after(0, lambda: messagebox.showinfo(
                        "Done",
                        f"Synced audio + subtitles merged into single file:\n{mkv_path}\n\n(This MKV contains the full PDF audio (including captions) with embedded, timed subtitles.)\n\nPlay in VLC or any media player that supports MKV subtitles for synced viewing."
                    ))
                else:
                    root.after(0, lambda: messagebox.showwarning(
                        "Fallback",
                        f"Merging failed (FFmpeg not available?).\n\nAudio saved to:\n{temp_audio}\nSubtitles saved to:\n{temp_srt}\n\nRename temp_audio.wav to your desired name if needed.\n\nInstall FFmpeg for automatic merging: https://ffmpeg.org/download.html"
                    ))
                root.after(0, lambda: status_label.config(text="Ready"))
            except Exception as e:
                for temp_file in [temp_audio, temp_srt]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Failed to generate audio: {e}\n\nSubtitles were not saved due to error."
                ))
                root.after(0, lambda: status_label.config(text="Error occurred"))
        status_label.config(text="Generating and merging audio + subtitles...")
        threading.Thread(target=run_generate, daemon=True).start()

def save_subtitles():
    if not current_text:
        messagebox.showwarning("Warning", "No text to save.")
        return
    save_path = filedialog.asksaveasfilename(
        defaultextension=".srt",
        filetypes=[("Subtitle File", "*.srt"), ("Text File", "*.txt")]
    )
    if save_path:
        try:
            paragraphs = re.split(r'\n\n+', current_text.strip())
            sentences = []
            for para in paragraphs:
                para_sentences = re.split(r'(?<=[.!?]) +', para)
                sentences.extend([s.strip() for s in para_sentences if s.strip()])
            with open(save_path, "w", encoding="utf-8") as f:
                time_cursor = 0.0
                for i, s in enumerate(sentences, 1):
                    if not s:
                        continue
                    words = s.split()
                    dur = max(1.0, len(words) * 0.4)
                    start = format_srt_time(time_cursor)
                    end = format_srt_time(time_cursor + dur)
                    f.write(f"{i}\n{start} --> {end}\n{s}\n\n")
                    time_cursor += dur
            messagebox.showinfo("Saved", f"Subtitles saved to:\n{save_path}\n(Includes all PDF captions and text with timings.)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

def format_srt_time(seconds):
    millis = int((seconds - int(seconds)) * 1000)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02},{millis:03}"

def toggle_theme():
    global theme_mode
    if theme_mode == "light":
        root.config(bg="#1e1e1e")
        left_frame.config(bg="#2c2c2c")
        right_frame.config(bg="#1e1e1e")
        subtitle_box.config(bg="#252526", fg="white", insertbackground="white")
        status_label.config(bg="#2c2c2c", fg="white")
        theme_mode = "dark"
    else:
        root.config(bg="SystemButtonFace")
        left_frame.config(bg="#f0f0f0")
        right_frame.config(bg="white")
        subtitle_box.config(bg="white", fg="black", insertbackground="black")
        status_label.config(bg="#f0f0f0", fg="black")
        theme_mode = "light"

# --- GUI ---
root = tk.Tk()
root.title("PDF to Audio Converter with OCR & Merged Subtitles (MKV)")
root.geometry("900x550")
root.resizable(False, True)

pdf_path = tk.StringVar()

frame = tk.Frame(root)
frame.pack(fill="both", expand=True)

# Left Panel
left_frame = tk.Frame(frame, width=250, bg="#f0f0f0")
left_frame.pack(side="left", fill="y", padx=10, pady=10)

# Right Panel
right_frame = tk.Frame(frame, bg="white")
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

tk.Label(left_frame, text="PDF to Audio Converter", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

tk.Button(left_frame, text="📂 Select PDF", command=select_pdf, width=20).pack(pady=5)
tk.Label(left_frame, textvariable=pdf_path, wraplength=200, fg="blue", bg="#f0f0f0").pack(pady=5)

tk.Label(left_frame, text="Select Voice:", bg="#f0f0f0").pack(pady=5)
voice_choice = ttk.Combobox(left_frame, values=["Male", "Female"], state="readonly", width=18)
voice_choice.set("Male")
voice_choice.pack(pady=5)

tk.Button(left_frame, text="▶ Play Audiobook", command=play_with_subtitles, width=20).pack(pady=5)
tk.Button(left_frame, text="💾 Download Audio + Subs", command=download_audio_and_subs, width=20).pack(pady=5)
tk.Button(left_frame, text="📝 Save Subtitles Only", command=save_subtitles, width=20).pack(pady=5)
tk.Button(left_frame, text="🌗 Toggle Theme", command=toggle_theme, width=20).pack(pady=5)
tk.Button(left_frame, text="⏹ Stop Playback", command=stop_playback, width=20).pack(pady=5)

status_label = tk.Label(left_frame, text="Ready", bg="#f0f0f0", fg="black", font=("Arial", 10))
status_label.pack(pady=10)

subtitle_box = tk.Text(right_frame, wrap="word", font=("Arial", 12), bg="white", fg="black", height=30)
subtitle_box.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()