import time
import os
import tempfile
import zipfile
import platform
import subprocess
from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                            TextClip, VideoFileClip)
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.audio_normalize import audio_normalize
import requests

def download_file(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url)
        f.write(response.content)

def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    program_path = search_program(program_name)
    return program_path

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    magick_path = get_program_path("magick")
    print(magick_path)
    if magick_path:
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
    else:
        os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'
    
    visual_clips = []
    for (t1, t2), video_url in background_video_data:
        # Download the video file
        video_filename = tempfile.NamedTemporaryFile(delete=False).name
        download_file(video_url, video_filename)

        # Check if the video file was downloaded properly
        if os.path.getsize(video_filename) == 0:
            print("Downloaded video file is empty:", video_filename)
            continue  # Handle the error appropriately

        # Create VideoFileClip from the downloaded file
        video_clip = VideoFileClip(video_filename)

        # Check if video_clip is valid
        if video_clip is None or video_clip.size == (0, 0):
            print("Failed to create video clip from:", video_filename)
            continue  # Handle the error appropriately

        # Resize video clip for 9:16 aspect ratio
        try:
            video_clip = video_clip.resize(newsize=(720, 1280))  # Resize to 720x1280 for 9:16
        except Exception as e:
            print(f"Error resizing video clip: {e}")
            continue  # Handle the error appropriately

        video_clip = video_clip.set_start(t1)
        video_clip = video_clip.set_end(t2)
        visual_clips.append(video_clip)

    audio_clips = []
    audio_file_clip = AudioFileClip(audio_file_path)
    audio_clips.append(audio_file_clip)

    for (t1, t2), text in timed_captions:
        # Create text clip with Tahoma font
        text_clip = TextClip(txt=text, fontsize=100, color="white", stroke_width=3, stroke_color="black", font="Tahoma", method="label")
        text_clip = text_clip.set_start(t1)
        text_clip = text_clip.set_end(t2)
        text_clip = text_clip.set_position(["center", 1000])  # Adjust position for 9:16 format
        visual_clips.append(text_clip)

    # Combine all video clips into one
    video = CompositeVideoClip(visual_clips)

    # Combine audio clips if any
    if audio_clips:
        audio = CompositeAudioClip(audio_clips)
        video.duration = audio.duration
        video.audio = audio

    # Write the final video file
    video.write_videofile(OUTPUT_FILE_NAME, codec='libx264', audio_codec='aac', fps=25, preset='veryfast')
    
    # Clean up downloaded files
    for (t1, t2), video_url in background_video_data:
        video_filename = tempfile.NamedTemporaryFile(delete=False).name
        os.remove(video_filename)

    return OUTPUT_FILE_NAME
