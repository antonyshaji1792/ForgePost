#!/usr/bin/env python3
"""
Video and Audio Merger
This program takes a video file and an audio file as input and merges them,
replacing the original audio with the provided audio file.
"""

import os
import sys
from pathlib import Path

def install_dependencies():
    """Install required dependencies if not already installed."""
    try:
        import moviepy
    except ImportError:
        print("Installing required package: moviepy...")
        os.system("pip install moviepy")
        print("moviepy installed successfully!")

def merge_video_audio(video_path, audio_path, output_path=None):
    """
    Merge video and audio files.
    
    Args:
        video_path (str): Path to the input video file
        audio_path (str): Path to the input audio file
        output_path (str, optional): Path for the output video file.
                                    If not provided, creates output in same directory as video
    
    Returns:
        bool: True if merge was successful, False otherwise
    """
    video = None
    audio = None
    video_with_new_audio = None
    
    try:
        # Import moviepy components
        from moviepy.editor import VideoFileClip, AudioFileClip
        import moviepy.audio.fx.all as afx
        
        # Validate input files exist
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            return False
        
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found: {audio_path}")
            return False
        
        print(f"Loading video file: {video_path}")
        video = VideoFileClip(video_path)
        
        print(f"Loading audio file: {audio_path}")
        audio = AudioFileClip(audio_path)
        
        # Check if audio duration matches or is longer than video duration
        video_duration = video.duration
        audio_duration = audio.duration
        
        print(f"Video duration: {video_duration:.2f} seconds")
        print(f"Audio duration: {audio_duration:.2f} seconds")
        
        if audio_duration < video_duration:
            print(f"Audio is shorter than video by {video_duration - audio_duration:.2f} seconds")
            print("Looping audio to match video duration.")
            # Use AudioLoop effect
            audio = audio.with_effects([afx.AudioLoop(duration=video_duration)])
        
        # Set the audio of the video to the new audio
        # Try with_audio (v2) first, fallback to set_audio (v1) if needed, though we expect v2
        if hasattr(video, 'with_audio'):
            video_with_new_audio = video.with_audio(audio)
        else:
            video_with_new_audio = video.set_audio(audio)
        
        # Generate output path if not provided
        if output_path is None:
            video_dir = os.path.dirname(video_path)
            video_name = Path(video_path).stem
            output_path = os.path.join(video_dir, f"{video_name}_with_new_audio.mp4")
        
        print(f"Merging files...")
        print(f"Output will be saved to: {output_path}")
        
        # Write the output video file
        video_with_new_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        print(f"Success! Video created: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error during merge: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Close the clips
        try:
            if video is not None:
                video.close()
            if audio is not None:
                audio.close()
            if video_with_new_audio is not None:
                video_with_new_audio.close()
        except Exception as e:
            print(f"Warning: Error closing files: {str(e)}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 3:
        print("Usage: python merge_video_audio.py <video_file> <audio_file> [output_file]")
        print("\nExample:")
        print("  python merge_video_audio.py video.mp4 audio.mp3 output.mp4")
        print("  python merge_video_audio.py video.mp4 audio.wav")
        print("\nSupported formats:")
        print("  Video: mp4, avi, mov, mkv, webm, flv, etc.")
        print("  Audio: mp3, wav, aac, m4a, flac, etc.")
        sys.exit(1)
    
    video_file = sys.argv[1]
    audio_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("=" * 60)
    print("Video and Audio Merger")
    print("=" * 60)
    
    # Install dependencies if needed
    install_dependencies()
    
    # Perform the merge
    success = merge_video_audio(video_file, audio_file, output_file)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
