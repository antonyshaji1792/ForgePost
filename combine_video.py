from moviepy.editor import VideoFileClip, concatenate_videoclips

def combine_videos(video1_path, video2_path, output_path):
    """
    Combines two video files into a single video file.

    Args:
        video1_path (str): The file path of the first video.
        video2_path (str): The file path of the second video.
        output_path (str): The desired file path for the combined video.
    """
    clip1 = VideoFileClip(video1_path)
    clip2 = VideoFileClip(video2_path)

    final_clip = concatenate_videoclips([clip1, clip2])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    clip1.close()
    clip2.close()

if __name__ == '__main__':
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(description="Combine two videos into one.")
    parser.add_argument("video1", nargs="?", help="Path to the first video file")
    parser.add_argument("video2", nargs="?", help="Path to the second video file")
    parser.add_argument("output", nargs="?", help="Path for the output combined video file")

    args = parser.parse_args()

    # Check if arguments are provided via command line
    if args.video1 and args.video2 and args.output:
        v1_path = args.video1
        v2_path = args.video2
        out_path = args.output
    else:
        # If not provided, ask for input interactively
        print("Enter the paths for the videos to combine.")
        v1_path = input("Path to first video: ").strip()
        while not os.path.exists(v1_path):
            print(f"Error: File '{v1_path}' not found.")
            v1_path = input("Path to first video: ").strip()

        v2_path = input("Path to second video: ").strip()
        while not os.path.exists(v2_path):
            print(f"Error: File '{v2_path}' not found.")
            v2_path = input("Path to second video: ").strip()
            
        out_path = input("Output file path (e.g., combined.mp4): ").strip()
        if not out_path:
            out_path = "combined_video.mp4"
            print(f"No output path provided. Defaulting to '{out_path}'")

    combine_videos(v1_path, v2_path, out_path)
