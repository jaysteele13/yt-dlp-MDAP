## Music Download Automation Pipeline

As I will be using [JP3 Organiser](https://github.com/jaysteele13/jp3_organiser) as my **local music storage tool**. Downloading music to then delete it can be **tedious**. Especially when we have to go through the effort to sort all songs, in order to find them efficiently.

It can take time. 🦥

This yt-dlp wrapper helps automate this process.

Instead of manually organising and creating files, this python app does it for us.

## Flow

1. Find YT Music we like.
2. Paste in the link to download.
3. MDAP then extracts the song/(s) metadata.
4. Organises it into Artist and Albums directories based on your set Music Directory Path
5. Also appends it to your Notion Database to keep a global discography of your music downloaded - in the cloud.


# Action Shots
<img width="989" height="757" alt="upload and save songs" src="https://github.com/user-attachments/assets/f582175e-cf23-44c8-b56c-de8e6ec4d35e" />
<img width="910" height="740" alt="image" src="https://github.com/user-attachments/assets/4f1262b5-8f54-41f0-a557-b67ecd547360" />
<img width="1409" height="453" alt="notion updated" src="https://github.com/user-attachments/assets/132e4267-ac87-4cff-90e0-fd9a7a36f9af" />

## How to install

### Requirements

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

### Install dependencies

```bash
pip install PyQt5 yt-dlp
```

Or install yt-dlp via your system package manager:

```bash
sudo apt install yt-dlp
```

### Run the application

```bash
python src/download_gui.py
```

Or as a module:

```bash
python -m src.download_gui
```