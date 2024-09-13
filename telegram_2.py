from telegram.ext import CommandHandler, MessageHandler, filters, ApplicationBuilder, CallbackContext
from spleeter.separator import Separator
from pydub import AudioSegment
from telegram import Update
from config import TOKEN
import noisereduce as nr
import numpy as np
import subprocess
import asyncio
import zipfile
import rarfile
import shutil
import wave
import os




MESSAGES = {
    'en': {
        'send_video': 'Please send a video file.',
        'download_video': 'Downloading the video...',
        'processing_video': 'Processing the video, please wait...',
        'voice_removed_success': 'Voice removed from video and file sent successfully!',
        'error_processing_video': 'Error processing the video.',
        'not_video': 'Received file is not a video. Please send a video file.',
        'no_processing_request': 'No video processing request found. Please use /remove_voice_from_video to start.',
        'receive_video_send_audio': 'Video received. Please send the audio file you want to add.',
        'processing_started': 'Processing started. Adding the new voice to the video.',
        'voice_added_success': 'Voice added to the video successfully!',
        'processing_completed': 'Processing completed. Saved to',
        'failed_create_video': 'Failed to create the new video file. Please check for errors.',
        'video_not_found': 'Video file not found. Please start again by sending a video file.'
    },
    'ar': {
        'send_video': 'يرجى إرسال ملف الفيديو.',
        'download_video': 'جاري تنزيل الفيديو...',
        'processing_video': 'جاري معالجة الفيديو، يرجى الانتظار...',
        'voice_removed_success': 'تم إزالة الصوت من الفيديو وتم إرسال الملف بنجاح!',
        'error_processing_video': 'حدث خطأ أثناء معالجة الفيديو.',
        'not_video': 'الملف المرسل ليس فيديو. يرجى إرسال ملف فيديو.',
        'no_processing_request': 'لم يتم العثور على طلب معالجة فيديو. يرجى استخدام /remove_voice_from_video للبدء.',
        'receive_video_send_audio': 'تم استلام الفيديو. يرجى إرسال ملف الصوت الذي ترغب في إضافته.',
        'processing_started': 'بدأت المعالجة. يتم إضافة الصوت الجديد إلى الفيديو.',
        'voice_added_success': 'تمت إضافة الصوت إلى الفيديو بنجاح!',
        'processing_completed': 'اكتملت المعالجة. تم الحفظ في',
        'failed_create_video': 'فشل في إنشاء ملف الفيديو الجديد. يرجى التحقق من الأخطاء.',
        'video_not_found': 'لم يتم العثور على ملف الفيديو. يرجى البدء مرة أخرى بإرسال ملف فيديو.'
    }
}


MESSAGES = {
    'en': {
        'send_video': 'Please send a video to remove and add new voice.',
        'receive_video_send_audio': 'Video received. Please send an audio file to add.',
        'processing_start_remove_voice': 'Processing started. Removing the original voice from the video.',
        'processing_start_add_voice': 'Adding the new voice to the video.',
        'processing_completed': 'Processing completed. Saved to',
        'file_creation_failed': 'Failed to create the new video file. Please check for errors.',
        'no_video_found': 'No video file found. Please start again by sending a video file.',
        'send_audio': 'Please send an audio file to clean noise.',
        'audio_received': 'Audio received. Processing now.',
        'conversion_failed': 'Failed to convert audio file. Please try again.',
        'cleaning_success': 'Cleaning completed successfully. File saved as',
        'processing_error': 'An error occurred during processing.',
        'no_audio_received': 'No audio file received. Please send an audio file.'
    },
    'ar': {
        'send_video': 'يرجى إرسال فيديو لإزالة وإضافة صوت جديد.',
        'receive_video_send_audio': 'تم استلام الفيديو. يرجى إرسال ملف صوتي لإضافته.',
        'processing_start_remove_voice': 'بدأت المعالجة. جاري إزالة الصوت الأصلي من الفيديو.',
        'processing_start_add_voice': 'جاري إضافة الصوت الجديد إلى الفيديو.',
        'processing_completed': 'تمت المعالجة. تم الحفظ إلى',
        'file_creation_failed': 'فشل في إنشاء ملف الفيديو الجديد. يرجى التحقق من الأخطاء.',
        'no_video_found': 'لم يتم العثور على ملف فيديو. يرجى البدء مرة أخرى بإرسال ملف فيديو.',
        'send_audio': 'يرجى إرسال ملف صوتي لتنظيف الضوضاء.',
        'audio_received': 'تم استلام الصوت. جاري المعالجة الآن.',
        'conversion_failed': 'فشل في تحويل ملف الصوت. يرجى المحاولة مرة أخرى.',
        'cleaning_success': 'تم تنظيف الصوت بنجاح. تم حفظ الملف كـ',
        'processing_error': 'حدث خطأ أثناء المعالجة.',
        'no_audio_received': 'لم يتم استلام ملف صوتي. يرجى إرسال ملف صوتي.'
    }
}

MESSAGES = {
    'en': {
        'send_video': 'Please send a video to clean noise.',
        'extracting_video': 'Extracting audio from the video...',
        'extracting_audio_failed': 'Failed to extract audio from the video.',
        'audio_cleaning': 'Cleaning the audio...',
        'extracting_audio_failed': 'Failed to extract audio.',
        'audio_cleaning': 'Cleaning the audio...',
        'merged_audio_video': 'Merging cleaned audio with video...',
        'clean_video_noice_success': 'Video noise cleaned successfully.',
        'no_video_found': 'No video found. Please send a video.',
    },
    'ar': {
        'send_video': 'يرجى إرسال فيديو لتنظيف الضوضاء.',
        'extracting_video': 'جاري استخراج الصوت من الفيديو...',
        'extracting_audio_failed': 'فشل في استخراج الصوت من الفيديو.',
        'audio_cleaning': 'جاري تنظيف الصوت...',
        'merged_audio_video': 'جاري دمج الصوت النظيف مع الفيديو...',
        'clean_video_noice_success': 'تم تنظيف الضوضاء من الفيديو بنجاح.',
        'no_video_found': 'لم يتم العثور على فيديو. يرجى إرسال فيديو.',
    }
}

def get_message(user_id, key):
    language = user_data.get(user_id, {}).get('language', 'en')
    return MESSAGES.get(language, {}).get(key, MESSAGES['en'].get(key, ''))

user_data = {}

SAVE_DIR = 'downloads'
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
def clean_up_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
def extract_rar(rar_path, extract_to):
    with rarfile.RarFile(rar_path, 'r') as rar_ref:
        rar_ref.extractall(extract_to)

async def set_language(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    args = context.args
    if not args:
        await update.message.reply_text("Please specify a language (ar/en).")
        return

    if args[0] in ['ar', 'en']:
        user_data[chat_id] = {'language': args[0]}
        await update.message.reply_text(MESSAGES[args[0]]['language_set'])
    else:
        await update.message.reply_text("Invalid language. Please use 'ar' or 'en'.")

async def set_language(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = context.args[0] if context.args else 'en'
    user_data[user_id] = {'language': language}
    await update.message.reply_text(f"Language set to {language}")

async def handle_file(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = user_data.get(user_id, {}).get('language', 'en')

    file = update.message.document
    file_ext = file.file_name.split('.')[-1].lower()
    file_path = os.path.join(SAVE_DIR, file.file_unique_id + '.' + file_ext)
    await file.get_file().download_to_drive(file_path)
    
    if file_ext in ['zip', 'rar']:
        extract_dir = os.path.join(SAVE_DIR, file.file_unique_id)
        os.makedirs(extract_dir, exist_ok=True)
        
        if file_ext == 'zip':
            extract_zip(file_path, extract_dir)
        elif file_ext == 'rar':
            extract_rar(file_path, extract_dir)
        
        # Find the first audio or video file in the archive
        audio_file_path = None
        video_file_path = None
        for root, _, files in os.walk(extract_dir):
            for filename in files:
                if filename.lower().endswith('.mp3'):
                    audio_file_path = os.path.join(root, filename)
                if filename.lower().endswith('.mp4'):
                    video_file_path = os.path.join(root, filename)
            if audio_file_path or video_file_path:
                break
        
        if not audio_file_path and not video_file_path:
            await update.message.reply_text(MESSAGES[language]['no_audio_found'])
            os.remove(file_path)
            return
    else:
        if file_ext in ['mp3', 'wav']:
            audio_file_path = file_path
            video_file_path = None
        elif file_ext in ['mp4']:
            audio_file_path = None
            video_file_path = file_path
        else:
            await update.message.reply_text(MESSAGES[language]['not_video'])
            os.remove(file_path)
            return

    await update.message.reply_text(f"{MESSAGES[language]['file_sent']} {file_path}")

async def process_large_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = user_data.get(user_id, {}).get('language', 'en')

    video_file = await update.message.video.get_file()
    file_info = await video_file.get_file()
    file_size = file_info.file_size

    size_limit = 100 * 1024 * 1024
    if file_size > size_limit:
        await update.message.reply_text(MESSAGES[language]['processing_video'])
        return

    video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
    await video_file.download_to_drive(video_file_path)

    segment_duration = 10  
    temp_files = []
    for i in range(0, int(file_size / (segment_duration * 1024 * 1024)) + 1):
        segment_file_path = os.path.join(SAVE_DIR, f'segment_{i}.mp4')
        temp_files.append(segment_file_path)
        command_split = f"ffmpeg -i {video_file_path} -ss {i*segment_duration} -t {segment_duration} -c copy {segment_file_path}"
        subprocess.call(command_split, shell=True)

    # Merge segmented files
    output_file_path = os.path.join(SAVE_DIR, 'merged_video.mp4')
    with open('filelist.txt', 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    command_merge = f"ffmpeg -f concat -safe 0 -i filelist.txt -c copy {output_file_path}"
    subprocess.call(command_merge, shell=True)

    # Clean up temporary files
    for temp_file in temp_files:
        os.remove(temp_file)
    os.remove('filelist.txt')
    os.remove(video_file_path)

    await update.message.reply_text(f"{MESSAGES[language]['processing_done']}")
    await update.message.reply_document(document=open(output_file_path, 'rb'))

    # Clean up directory
    clean_up_directory(SAVE_DIR)

async def handle_user_state(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = user_data.get(user_id, {}).get('language', 'en')
    
    if user_id in user_data:
        state = user_data[user_id]['state']

        if state == 'waiting_for_video_to_remove_voice':
            await remove_voice_from_video_process(update, context)
        elif state == 'waiting_for_video_to_add_voice':
            await add_voice_to_video_process(update, context)
        elif state == 'waiting_for_audio_to_add_voice':
            await add_voice_to_video_process_audio(update, context)
        elif state == 'waiting_for_video_to_remove_add_voice':
            await remove_add_voice_to_video_process(update, context)
        elif state == 'waiting_for_audio_to_remove_add_voice':
            await remove_add_voice_to_video_process_audio(update, context)
        elif state == 'waiting_for_audio_to_clean_noise':
            await clean_noise_from_audio_process(update, context)
        elif state == 'waiting_for_video_to_clean_noise':
            await clean_noise_from_video_process(update, context)
        else:
            await update.message.reply_text(MESSAGES[language]['unknown_state'])
    else:
        await update.message.reply_text(MESSAGES[language]['unknown_state'])

async def remove_voice_from_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_video_to_remove_voice'}
    language = user_data.get(user_id, {}).get('language', 'en')
    await update.message.reply_text(MESSAGES[language]['send_video'])
async def remove_voice_from_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = user_data.get(user_id, {}).get('language', 'en')
    
    if user_id in user_data and user_data[user_id]['state'] == 'waiting_for_video_to_remove_voice':
        if update.message.video:
            await update.message.reply_text(MESSAGES[language]['download_video'])

            video_file = await update.message.video.get_file()
            video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')

            await video_file.download_to_drive(video_file_path)
            await update.message.reply_text(MESSAGES[language]['processing_video'])

            output_file_path = video_file_path.replace('.mp4', '_no_voice.mp4')
            command = f"ffmpeg -i {video_file_path} -c:v copy -an {output_file_path}"
            subprocess.run(command, shell=True)

            if os.path.exists(output_file_path):
                await update.message.reply_document(document=open(output_file_path, 'rb'))
                await update.message.reply_text(MESSAGES[language]['voice_removed_success'])
            else:
                await update.message.reply_text(MESSAGES[language]['error_processing_video'])
            
            clean_up_directory(SAVE_DIR)
            del user_data[user_id]  
        else:
            await update.message.reply_text(MESSAGES[language]['not_video'])
    else:
        await update.message.reply_text(MESSAGES[language]['no_processing_request'])

async def add_voice_to_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_video_to_add_voice'}
    language = user_data.get(user_id, {}).get('language', 'en')
    await update.message.reply_text(MESSAGES[language]['send_video'])
async def add_voice_to_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = user_data.get(user_id, {}).get('language', 'en')
    
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_video_to_add_voice":
        video_file = update.message.video
        file = await video_file.get_file()

        video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')  
        await file.download_to_drive(video_file_path)

        user_data[update.message.from_user.id] = {'video_file_path': video_file_path, 'state': 'waiting_for_audio_to_add_voice'}
        await update.message.reply_text(MESSAGES[language]['receive_video_send_audio'])
async def add_voice_to_video_process_audio(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    language = user_data.get(user_id, {}).get('language', 'en')
    
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_audio_to_add_voice":
        audio_file = await update.message.audio.get_file()
        audio_file_path = os.path.join(SAVE_DIR, f'{update.message.audio.file_unique_id}.mp3')
        await audio_file.download_to_drive(audio_file_path)

        user_info = user_data.get(update.message.from_user.id, {})
        video_file_path = user_info.get('video_file_path') 

        if video_file_path:
            output_file_path = video_file_path.replace('.mp4', '_with_new_voice.mp4')

            if not os.path.exists(video_file_path):
                await update.message.reply_text(MESSAGES[language]['video_not_found'])
                return

            await update.message.reply_text(MESSAGES[language]['processing_started'])

            command_add_voice = (
                f"ffmpeg -i {video_file_path} -stream_loop -1 -i {audio_file_path} "
                f"-c:v copy -map 0:v:0 -map 1:a:0 -shortest {output_file_path}"
            )

            result = subprocess.run(command_add_voice, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print("Error adding voice:", result.stderr)
                return

            await update.message.reply_text(MESSAGES[language]['voice_added_success'])

            if os.path.exists(output_file_path):
                await update.message.reply_text(f"{MESSAGES[language]['processing_completed']} {output_file_path}")
                await update.message.reply_document(document=open(output_file_path, 'rb'))
            else:
                await update.message.reply_text(MESSAGES[language]['failed_create_video'])

            clean_up_directory(SAVE_DIR)
            return
        else:
            await update.message.reply_text(MESSAGES[language]['no_video_found'])

def get_message(user_id, key):
    language = user_data.get(user_id, {}).get('language', 'en')
    return MESSAGES.get(language, {}).get(key, MESSAGES['en'].get(key, ''))
async def remove_add_voice_to_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_video_to_remove_add_voice'}
    await update.message.reply_text(get_message(user_id, 'send_video'))

async def remove_add_voice_to_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_video_to_remove_add_voice":
        video_file = update.message.video
        file_info = await video_file.get_file()
        file_size = file_info.file_size

        size_limit = 50 * 1024 * 1024  # 50 MB

        if file_size > size_limit:
            await process_large_video(update, context)
            return

        video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
        await video_file.download_to_drive(video_file_path)
        user_data[user_id] = {'video_file_path': video_file_path, 'state': 'waiting_for_audio_to_remove_add_voice'}
        await update.message.reply_text(get_message(user_id, 'receive_video_send_audio'))

async def remove_add_voice_to_video_process_audio(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_audio_to_remove_add_voice":
        audio_file = await update.message.audio.get_file()
        audio_file_path = os.path.join(SAVE_DIR, f'{update.message.audio.file_unique_id}.mp3')
        await audio_file.download_to_drive(audio_file_path)

        user_info = user_data.get(user_id, {})
        video_file_path = user_info.get('video_file_path')

        if video_file_path:
            temp_no_voice_video_path = video_file_path.replace('.mp4', '_no_voice.mp4')
            temp_audio_path = "temp_audio.mp3"
            output_file_path = video_file_path.replace('.mp4', '_with_new_voice.mp4')

            await update.message.reply_text(get_message(user_id, 'processing_start_remove_voice'))

            command_remove_voice = f"ffmpeg -i {video_file_path} -c:v copy -an {temp_no_voice_video_path}"
            subprocess.run(command_remove_voice, shell=True)

            # Export audio to a temporary file
            audio_clip = AudioSegment.from_file(audio_file_path)
            audio_clip.export(temp_audio_path, format="mp3")

            await update.message.reply_text(get_message(user_id, 'processing_start_add_voice'))

            # Add new voice to the video
            command_add_voice = (
                f"ffmpeg -i {temp_no_voice_video_path} -stream_loop -1 -i {temp_audio_path} "
                f"-c:v copy -map 0:v:0 -map 1:a:0 -shortest {output_file_path}")

            subprocess.run(command_add_voice, shell=True)

            # Clean up temporary files
            os.remove(temp_no_voice_video_path)
            os.remove(temp_audio_path)
            os.remove(video_file_path)
            os.remove(audio_file_path)

            if os.path.exists(output_file_path):
                await update.message.reply_text(get_message(user_id, 'processing_completed') + f" {output_file_path}")
                await update.message.reply_document(document=open(output_file_path, 'rb'))
            else:
                await update.message.reply_text(get_message(user_id, 'file_creation_failed'))

            clean_up_directory(SAVE_DIR)
        else:
            await update.message.reply_text(get_message(user_id, 'no_video_found'))

async def clean_noise_from_audio(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_audio_to_clean_noise'}
    await update.message.reply_text(get_message(user_id, 'send_audio'))

async def clean_noise_from_audio_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_audio_to_clean_noise":
        if update.message.audio:
            try:
                # Download the audio file
                audio_file = update.message.audio
                file = await audio_file.get_file()
                audio_file_path = os.path.join(SAVE_DIR, f'{audio_file.file_unique_id}.mp3')
                await file.download_to_drive(audio_file_path)
                await update.message.reply_text(get_message(user_id, 'audio_received'))

                # Convert audio file to WAV
                temp_audio_path = "temp_audio.wav"
                command_convert_audio = f"ffmpeg -i \"{audio_file_path}\" {temp_audio_path}"
                await asyncio.create_subprocess_shell(command_convert_audio)

                if not os.path.exists(temp_audio_path):
                    await update.message.reply_text(get_message(user_id, 'conversion_failed'))
                    return

                # Use Spleeter to separate vocals from accompaniment
                separator = Separator('spleeter:2stems')  # Use 2stems model
                spleeter_output_dir = os.path.join(SAVE_DIR, 'spleeter_output')
                separator.separate_to_file(temp_audio_path, spleeter_output_dir)

                # Paths for separated files
                vocals_path = os.path.join(spleeter_output_dir, 'vocals.wav')
                accompaniment_path = os.path.join(spleeter_output_dir, 'accompaniment.wav')

                # Clean the vocals audio
                with wave.open(vocals_path, 'rb') as wf:
                    rate = wf.getframerate()
                    channels = wf.getnchannels()
                    width = wf.getsampwidth()
                    chunk_size = 1024 * 1024
                    data = wf.readframes(chunk_size)
                    cleaned_data = []

                    while data:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        cleaned_chunk = nr.reduce_noise(y=audio_array, sr=rate)
                        cleaned_data.append(cleaned_chunk)
                        data = wf.readframes(chunk_size)

                    cleaned_audio = np.concatenate(cleaned_data)
                    cleaned_vocals_path = vocals_path.replace('.wav', '_cleaned.wav')

                    with wave.open(cleaned_vocals_path, 'wb') as cleaned_wf:
                        cleaned_wf.setnchannels(channels)
                        cleaned_wf.setsampwidth(width)
                        cleaned_wf.setframerate(rate)
                        cleaned_wf.writeframes(cleaned_audio.tobytes())

                # Convert cleaned audio to MP3
                output_file_path = audio_file_path.replace('.mp3', '_cleaned.mp3')
                command_convert_cleaned_audio = f"ffmpeg -i \"{cleaned_vocals_path}\" {output_file_path}"
                await asyncio.create_subprocess_shell(command_convert_cleaned_audio)

                # Clean up temporary files
                os.remove(temp_audio_path)
                os.remove(cleaned_vocals_path)

                await update.message.reply_text(get_message(user_id, 'cleaning_success') + f" {output_file_path}")
                await update.message.reply_document(document=open(output_file_path, 'rb'))

            except Exception as e:
                await update.message.reply_text(get_message(user_id, 'processing_error') + f" {str(e)}")
        else:
            await update.message.reply_text(get_message(user_id, 'no_audio_received'))
        
        clean_up_directory(SAVE_DIR)

async def clean_noise_from_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_video_to_clean_noise'}
    await update.message.reply_text(get_message(user_id, 'send_video'))

async def clean_noise_from_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_video_to_clean_noise":
        if update.message.video:
            try:
                video_file = await update.message.video.get_file()
                video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
                await video_file.download_to_drive(video_file_path)

                await update.message.reply_text(get_message(user_id, 'extracting_video'))

                temp_audio_path = "temp_audio.wav"
                output_file_path = video_file_path.replace('.mp4', '_cleaned.mp4')

                # Extract audio asynchronously using ffmpeg
                command_extract_audio = f"ffmpeg -i \"{video_file_path}\" -q:a 0 -map a {temp_audio_path}"
                await asyncio.create_subprocess_shell(command_extract_audio)

                if not os.path.exists(temp_audio_path):
                    await update.message.reply_text(get_message(user_id, 'extracting_audio_failed'))
                    return

                await update.message.reply_text(get_message(user_id, 'audio_cleaning'))

                # Use Spleeter to separate vocals and accompaniment
                separator = Separator('spleeter:2stems')  # Two stems model: vocals and accompaniment
                spleeter_output_dir = os.path.join(SAVE_DIR, 'spleeter_output')
                separator.separate_to_file(temp_audio_path, spleeter_output_dir)

                # Spleeter output paths
                vocals_path = os.path.join(spleeter_output_dir, 'vocals.wav')
                accompaniment_path = os.path.join(spleeter_output_dir, 'accompaniment.wav')

                # Clean vocals using noisereduce
                with wave.open(vocals_path, 'rb') as wf:
                    rate = wf.getframerate()
                    channels = wf.getnchannels()
                    width = wf.getsampwidth()
                    cleaned_data = []
                    chunk_size = 1024 * 1024
                    data = wf.readframes(chunk_size)

                    while data:
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        cleaned_chunk = nr.reduce_noise(y=audio_array, sr=rate)
                        cleaned_data.append(cleaned_chunk)
                        data = wf.readframes(chunk_size)

                    cleaned_audio = np.concatenate(cleaned_data)
                    cleaned_vocals_path = vocals_path.replace('.wav', '_cleaned.wav')

                    with wave.open(cleaned_vocals_path, 'wb') as cleaned_wf:
                        cleaned_wf.setnchannels(channels)
                        cleaned_wf.setsampwidth(width)
                        cleaned_wf.setframerate(rate)
                        cleaned_wf.writeframes(cleaned_audio.tobytes())

                await update.message.reply_text(get_message(user_id, 'merged_audio_video'))

                # Merge cleaned vocals with original video
                command_add_cleaned_audio = f"ffmpeg -i \"{video_file_path}\" -i \"{cleaned_vocals_path}\" -c:v copy -map 0:v:0 -map 1:a:0 {output_file_path}"
                await asyncio.create_subprocess_shell(command_add_cleaned_audio)

                # Clean up temporary files
                os.remove(temp_audio_path)
                os.remove(cleaned_vocals_path)

                await update.message.reply_text(get_message(user_id, 'clean_video_noice_success'))
                await update.message.reply_document(document=open(output_file_path, 'rb'))

            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")
        else:
            await update.message.reply_text(get_message(user_id, 'no_video_found'))

        clean_up_directory()

async def handle_non_command_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Please click /start to begin the process and wait")


def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('remove_voice_video', remove_voice_from_video))
    application.add_handler(CommandHandler('add_voice_video', add_voice_to_video))
    application.add_handler(CommandHandler('remove_add_voice_video', remove_add_voice_to_video))
    application.add_handler(CommandHandler('clean_noise_audio', clean_noise_from_audio))
    application.add_handler(CommandHandler('clean_noise_video', clean_noise_from_video))
    application.add_handler(CommandHandler('set_language', set_language, pass_args=True))

    # Message handlers
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_command_message))
    application.add_handler(MessageHandler(filters.VIDEO, handle_user_state))
    application.add_handler(MessageHandler(filters.AUDIO, handle_user_state))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
