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

# Function to download files
def download_file(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url)
        f.write(response.content)

# Function to search for program (like ImageMagick)
def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

# Get the program path
def get_program_path(program_name):
    program_path = search_program(program_name)
    return program_path

# Main function to render the video with captions
def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    magick_path = get_program_path("magick")
    print(magick_path)
    
    if magick_path:
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
    else:
        os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'

    visual_clips = []
    
    # Process each background video URL
    for (t1, t2), video_url in background_video_data:
        # Download the video file
        video_filename = tempfile.NamedTemporaryFile(delete=False).name
        download_file(video_url, video_filename)

        # Check if the video file was downloaded properly
        if os.path.getsize(video_filename) == 0:
            print("Downloaded video file is empty:", video_filename)
            continue  # Skip to the next video

        # Create a VideoFileClip from the downloaded file
        video_clip = VideoFileClip(video_filename)

        # Check if the video_clip is valid
        if video_clip is None or video_clip.size == (0, 0):
            print("Failed to create video clip from:", video_filename)
            continue

        # Resize video clip for 9:16 aspect ratio (720x1280)
        try:
            video_clip = video_clip.resize(newsize=(720, 1280))
        except Exception as e:
            print(f"Error resizing video clip: {e}")
            continue

        video_clip = video_clip.set_start(t1).set_end(t2)
        visual_clips.append(video_clip)

    audio_clips = []
    audio_file_clip = AudioFileClip(audio_file_path)
    audio_clips.append(audio_file_clip)

    # Add captions as text overlays
    for (t1, t2), text in timed_captions:
        text_clip = TextClip(
            txt=text,
            fontsize=100,  # Font size
            color="white",  # Text color
            stroke_width=3,  # Outline width
            stroke_color="black",  # Outline color
            font="Tahoma",  # Font style set to Tahoma
            method="label"
        )
        text_clip = text_clip.set_start(t1).set_end(t2).set_position(("center", 800))
        visual_clips.append(text_clip)

    # Create the final video by combining clips
    video = CompositeVideoClip(visual_clips)

    if audio_clips:
        audio = CompositeAudioClip(audio_clips)
        video.duration = audio.duration
        video.audio = audio

    # Write the final output to a file
    video.write_videofile(OUTPUT_FILE_NAME, codec='libx264', audio_codec='aac', fps=25, preset='veryfast')

    # Clean up downloaded video files
    for (t1, t2), video_url in background_video_data:
        video_filename = tempfile.NamedTemporaryFile(delete=False).name
        os.remove(video_filename)

    return OUTPUT_FILE_NAME
