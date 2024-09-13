import os
import zipfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from pydub.silence import split_on_silence
import subprocess
from telegram import TOKEN

# Directory to save the files
SAVE_DIR = 'downloads'
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

async def start(update: Update, context):
    await update.message.reply_text(
        "Send me a video or audio file, and I'll save it! You can also use the following commands:\n"
        "/clean_noise_audio - Clean noise from audio\n"
        "/remove_voice_video - Remove voice from video\n"
        "/add_voice_video - Add voice to video"
    )

async def handle_file(update: Update, context):
    user_id = update.message.from_user.id
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    file_ext = os.path.splitext(file_name)[1]

    if file_ext == '.zip':
        zip_file = await update.message.document.get_file()
        zip_file_path = os.path.join(SAVE_DIR, f'{file_id}.zip')
        await zip_file.download_to_drive(zip_file_path)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(SAVE_DIR)
        os.remove(zip_file_path)  # Remove the ZIP file after extraction

        # Find the extracted files
        for extracted_file in os.listdir(SAVE_DIR):
            if extracted_file.endswith('.mp4'):
                video_file_path = os.path.join(SAVE_DIR, extracted_file)
                await update.message.reply_text(f"Video extracted and saved to {video_file_path}")
            elif extracted_file.endswith('.mp3'):
                audio_file_path = os.path.join(SAVE_DIR, extracted_file)
                await update.message.reply_text(f"Audio extracted and saved to {audio_file_path}")

    else:
        # Handle regular video and audio files
        file_path = os.path.join(SAVE_DIR, f'{file_id}{file_ext}')
        await update.message.document.download_to_drive(file_path)
        if file_ext == '.mp4':
            await update.message.reply_text(f"Video saved to {file_path}")
        elif file_ext == '.mp3':
            await update.message.reply_text(f"Audio saved to {file_path}")

async def clean_noise_audio(update: Update, context):
    audio_file_path = os.path.join(SAVE_DIR, f'{update.message.audio.file_unique_id}.mp3')
    
    if os.path.exists(audio_file_path):
        audio = AudioSegment.from_file(audio_file_path)
        chunks = split_on_silence(audio, min_silence_len=500, silence_thresh=-40)
        cleaned_audio = sum(chunks)
        cleaned_file_path = audio_file_path.replace('.mp3', '_cleaned.mp3')
        cleaned_audio.export(cleaned_file_path, format="mp3")
        await update.message.reply_text(f"Noise cleaned. Saved to {cleaned_file_path}")
    else:
        await update.message.reply_text("Audio file not found.")

async def remove_voice_video(update: Update, context):
    video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
    
    if os.path.exists(video_file_path):
        output_file_path = video_file_path.replace('.mp4', '_no_voice.mp4')
        command = f"ffmpeg -i {video_file_path} -an {output_file_path}"
        subprocess.call(command, shell=True)
        await update.message.reply_text(f"Voice removed from video. Saved to {output_file_path}")
    else:
        await update.message.reply_text("Video file not found.")

async def add_voice_video(update: Update, context):
    video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
    audio_file_path = os.path.join(SAVE_DIR, f'{update.message.audio.file_unique_id}.mp3')
    
    if os.path.exists(video_file_path) and os.path.exists(audio_file_path):
        output_file_path = video_file_path.replace('.mp4', '_with_voice.mp4')
        video_clip = VideoFileClip(video_file_path)
        audio_clip = AudioSegment.from_file(audio_file_path)
        audio_clip.export("temp_audio.mp3", format="mp3")
        command = f"ffmpeg -i {video_file_path} -i temp_audio.mp3 -c:v copy -map 0:v:0 -map 1:a:0 {output_file_path}"
        subprocess.call(command, shell=True)
        os.remove("temp_audio.mp3")
        await update.message.reply_text(f"Voice added to video. Saved to {output_file_path}")
    else:
        await update.message.reply_text("Video or audio file not found.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Command to start the bot
    application.add_handler(CommandHandler('start', start))

    # Commands for noise cleaning and voice editing
    application.add_handler(CommandHandler('clean_noise_audio', clean_noise_audio))
    application.add_handler(CommandHandler('remove_voice_video', remove_voice_video))
    application.add_handler(CommandHandler('add_voice_video', add_voice_video))

    # Handler for files
    application.add_handler(MessageHandler(filters.Document.ALL & ~filters.Document.MP4 & ~filters.Document.MP3, handle_file))
    application.add_handler(MessageHandler(filters.VIDEO, handle_file))
    application.add_handler(MessageHandler(filters.AUDIO, handle_file))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
