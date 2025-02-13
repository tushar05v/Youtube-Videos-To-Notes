# YouTube to Notes - Transcription and Audio Player

This project is a GUI-based application that allows users to download audio from YouTube videos, transcribe the audio using Whisper AI, and play the transcribed audio using an integrated audio player.

## Features
- Download audio from YouTube
- Transcribe the downloaded audio
- Save transcriptions as text notes
- Integrated audio player with play, pause, and seek functionality
- API key management for transcription services

## Installation
### Prerequisites
- Python 3.8+
- Install dependencies using pip:
  ```bash
  pip install -r requirements.txt
  ```

## Usage
1. Run the script:
   ```bash
   python main.py
   ```
2. Enter a YouTube URL and click "Download and Transcribe."
3. The transcription will be displayed once the process is complete.
4. Use the integrated player to listen to the audio.

---

## Function Breakdown

<details>
  <summary><b>adjust_height</b></summary>

  ```python
  def adjust_height(event=None):
      lines = int(audio_title.index('end-1c').split('.')[0])
      audio_title.config(height=lines)
  ```
  
  Adjusts the height of the text widget dynamically based on the number of lines.
</details>

<details>
  <summary><b>init_audio_player</b></summary>

  ```python
  def init_audio_player():
      mixer.init()
  ```
  
  Initializes the Pygame mixer for audio playback.
</details>

<details>
  <summary><b>load_audio</b></summary>

  ```python
  def load_audio(file_path):
      global audio_length, current_position
      mixer.music.load(file_path)
      audio_length = mixer.Sound(file_path).get_length()
      current_position = 0
      slider.config(to=audio_length)
      slider.set(0)
      update_time_display(0)
  ```
  
  Loads an audio file and updates the UI components accordingly.
</details>

<details>
  <summary><b>toggle_play_pause</b></summary>

  ```python
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
  ```
  
  Toggles between play and pause states for audio playback.
</details>

<details>
  <summary><b>download_audio</b></summary>

  ```python
  def download_audio(url):
      dire = os.getcwd() if current_dir else tempfile.gettempdir()
      outtmpl = os.path.join(dire, "%(title)s.%(ext)s") if current_dir else os.path.join(dire, "downloaded_audio.%(ext)s")
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
      with yt_dlp.YoutubeDL(options) as ydl:
          info = ydl.extract_info(url, download=True)
          title = info.get('title', 'downloaded_audio')
      return os.path.join(dire, f"{title}.mp3")
  ```
  
  Downloads the audio from a YouTube video and saves it as an MP3 file.
</details>

<details>
  <summary><b>transcribe_audio</b></summary>

  ```python
  def transcribe_audio(url):
      if not url:
          messagebox.showerror("Error", "Please enter a YouTube URL")
          return
      try:
          audio_path = download_audio(url)
          model = whisper.load_model("base")
          result = model.transcribe(audio_path)
          transcription = gemini_update(f"Clean and convert this transcription into good notes: {result['text']}")
          type_text(transcribe_text, transcription)
      except Exception as e:
          messagebox.showerror("Error", str(e))
  ```
  
  Transcribes the downloaded audio using Whisper AI and formats it using Gemini AI.
</details>

## Contributing
Feel free to submit pull requests or report issues.

## License
This project is licensed under the MIT License.

