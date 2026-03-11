from moviepy.editor import VideoFileClip
import argparse
import os
import sys

def trim_video(video_path, start_time, end_time, output_path):
    """
    Trims a video file from start_time to end_time.

    Args:
        video_path (str): Path to the input video.
        start_time (float): Start time in seconds.
        end_time (float): End time in seconds.
        output_path (str): Path for the output video.
    """
    try:
        clip = VideoFileClip(video_path)
        
        # Validate times
        if start_time < 0:
            start_time = 0
        if end_time > clip.duration:
            print(f"Warning: End time {end_time} exceeds video duration {clip.duration}. Trimming to end.")
            end_time = clip.duration
        if start_time >= end_time:
            print("Error: Start time must be less than end time.")
            return

        trimmed_clip = clip.subclipped(start_time, end_time)
        trimmed_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        clip.close()
        print(f"Successfully created trimmed video: {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trim a video file based on start and end seconds.")
    parser.add_argument("video_path", nargs="?", help="Path to the input video file")
    parser.add_argument("start_time", nargs="?", type=float, help="Start time in seconds")
    parser.add_argument("end_time", nargs="?", type=float, help="End time in seconds")
    parser.add_argument("output_path", nargs="?", help="Path for the output trimmed video")

    args = parser.parse_args()

    # Check if arguments are provided via command line
    if args.video_path and args.start_time is not None and args.end_time is not None and args.output_path:
        v_path = args.video_path
        start = args.start_time
        end = args.end_time
        out_path = args.output_path
    else:
        print("Enter the details to trim the video.")
        
        v_path = input("Path to video file: ").strip()
        while not os.path.exists(v_path):
            print(f"Error: File '{v_path}' not found.")
            v_path = input("Path to video file: ").strip()

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

        out_path = input("Output file path (e.g., trimmed.mp4): ").strip()
        if not out_path:
            base, ext = os.path.splitext(v_path)
            out_path = f"{base}_trimmed{ext}"
            print(f"No output path provided. Defaulting to '{out_path}'")

    trim_video(v_path, start, end, out_path)
