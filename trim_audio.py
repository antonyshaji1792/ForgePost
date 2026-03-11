from moviepy.editor import AudioFileClip
import argparse
import os
import sys

def trim_audio(audio_path, start_time, end_time, output_path):
    """
    Trims an audio file from start_time to end_time.

    Args:
        audio_path (str): Path to the input audio.
        start_time (float): Start time in seconds.
        end_time (float): End time in seconds.
        output_path (str): Path for the output audio.
    """
    try:
        clip = AudioFileClip(audio_path)
        
        # Validate times
        if start_time < 0:
            start_time = 0
        if end_time > clip.duration:
            print(f"Warning: End time {end_time} exceeds audio duration {clip.duration}. Trimming to end.")
            end_time = clip.duration
        if start_time >= end_time:
            print("Error: Start time must be less than end time.")
            return

        trimmed_clip = clip.subclipped(start_time, end_time)
        # Determine codec based on output extension
        _, ext = os.path.splitext(output_path)
        codec = None
        if ext.lower() == '.mp3':
            codec = 'libmp3lame'
        elif ext.lower() in ['.m4a', '.aac', '.mp4']:
            codec = 'aac'
        # For wav, moviepy defaults to pcm_s16le which is fine.
        
        # Write file with appropriate codec
        if codec:
            trimmed_clip.write_audiofile(output_path, codec=codec)
        else:
            trimmed_clip.write_audiofile(output_path) # Let moviepy decide
        
        clip.close()
        print(f"Successfully created trimmed audio: {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trim an audio file based on start and end seconds.")
    parser.add_argument("audio_path", nargs="?", help="Path to the input audio file")
    parser.add_argument("start_time", nargs="?", type=float, help="Start time in seconds")
    parser.add_argument("end_time", nargs="?", type=float, help="End time in seconds")
    parser.add_argument("output_path", nargs="?", help="Path for the output trimmed audio")

    args = parser.parse_args()

    # Check if arguments are provided via command line
    if args.audio_path and args.start_time is not None and args.end_time is not None and args.output_path:
        a_path = args.audio_path
        start = args.start_time
        end = args.end_time
        out_path = args.output_path
    else:
        print("Enter the details to trim the audio.")
        
        a_path = input("Path to audio file: ").strip()
        while not os.path.exists(a_path):
            print(f"Error: File '{a_path}' not found.")
            a_path = input("Path to audio file: ").strip()

        while True:
            try:
                start = float(input("Start time (seconds): ").strip())
                if start < 0:
                    print("Start time cannot be negative.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number for start time.")

        while True:
            try:
                end = float(input("End time (seconds): ").strip())
                if end <= start:
                    print("End time must be greater than start time.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number for end time.")

        out_path = input("Output file path (e.g., trimmed.mp3): ").strip()
        if not out_path:
            base, ext = os.path.splitext(a_path)
            out_path = f"{base}_trimmed{ext}"
            print(f"No output path provided. Defaulting to '{out_path}'")

    trim_audio(a_path, start, end, out_path)
