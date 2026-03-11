import asyncio
import edge_tts
import sys

async def _generate(text, voice, rate, output_file):
    """
    Generate TTS audio using edge-tts.
    
    Args:
        text (str): Input text
        voice (str): Voice ID (e.g., 'en-US-AriaNeural')
        rate (str): Rate string (e.g., '+0%', '+50%')
        output_file (str): Output file path
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

def text_to_speech(text, voice, speed_float, output_file):
    """
    Wrapper to run async generation synchronously.
    
    Args:
        text (str): Input text
        voice (str): Voice ID
        speed_float (float): Speed multiplier (e.g. 1.0, 1.5, 0.8)
        output_file (str): Output file path
    """
    # Logging setup
    with open("tts_debug.log", "a", encoding="utf-8") as f:
        f.write(f"In text_to_speech: text='{text[:20]}...', voice={voice}, speed={speed_float}, out={output_file}\n")

    # Convert float speed to percentage string
    percentage = int((speed_float - 1.0) * 100)
    if percentage >= 0:
        rate_str = f"+{percentage}%"
    else:
        rate_str = f"{percentage}%"
    
    try:
        asyncio.run(_generate(text, voice, rate_str, output_file))
        with open("tts_debug.log", "a", encoding="utf-8") as f:
            f.write("Audio generation successful\n")
    except Exception as e:
        with open("tts_debug.log", "a", encoding="utf-8") as f:
            f.write(f"Error in text_to_speech: {str(e)}\n")
        raise e

if __name__ == "__main__":
    # Test
    text_to_speech("Hello this is a test.", "en-US-AriaNeural", 1.0, "test_tts.mp3")
    print("Created test_tts.mp3")
