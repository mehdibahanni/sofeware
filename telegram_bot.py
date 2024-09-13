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
    'ar':{
        'send_video': 'يرجى إرسال ملف الفيديو...',
        'receive_video_send_audio': 'تم استلام الفيديو. الآن، يرجى إرسال ملف الصوت.',
        'start': 'مرحبًا! يرجى اختيار خيار أدناه:',        
        'download_video': 'يتم تنزيل الفيديو، يرجى الانتظار...',
        'processing_video': 'يتم معالجة الفيديو، يرجى الانتظار...',
        'send_audio': 'يرجى إرسال ملف الصوت...',
        'audio_received': 'تم استلام ملف الصوت. جاري المعالجة...',
        'video_received': 'تم استلام الفيديو. الآن، يرجى إرسال ملف الصوت.',
        'processing_done': 'اكتملت المعالجة!',
        'file_sent': 'تم إرسال الملف بنجاح!',
        'not_video': 'الملف المستلم ليس فيديو. يرجى إرسال ملف فيديو.',
        'no_video_found': 'لم يتم العثور على ملف الفيديو. يرجى البدء من جديد بإرسال ملف الفيديو.',
        'add_voice_success': 'تمت إضافة الصوت إلى الفيديو بنجاح!',
        'remove_voice_success': 'تمت إزالة الصوت من الفيديو وتم إرسال الملف بنجاح!',
        'send_file_error': 'حدث خطأ أثناء معالجة الملف.',
        'clean_video_noice_success': 'تم تنظيف الفيديو من الضوضاء !',
        'merged_audio_video': 'تم تنظيف الصوت بنجاح. جاري دمج الصوت النظيف مع الفيديو...',
        'language_set': 'تم تعيين اللغة إلى العربية!', 
        'extracting_audio': 'تم استلام ملف الفيديو. جاري استخراج الصوت...',
        'extracting_audio_failed': 'فشل استخراج الصوت. لم يتم إنشاء ملف الصوت.',
        'audio_cleaning': 'تم استخراج الصوت بنجاح. جاري تنظيف الصوت...',
        'audio_received': "تم استلام ملف الصوت. جاري تنظيف الصوت...",
        'conversion_failed': "فشل تحويل الصوت إلى صيغة WAV.",
        'processing_error': "حدث خطأ أثناء معالجة الصوت:",
        'cleaning_success': "تم تنظيف الصوت بنجاح. تم حفظ الملف باسم ",
        'no_audio_received': "لم يتم استلام ملف صوت.",
        'cleaning_started': "تم بدء تنظيف الصوت...",        
    },
    'en':{
        'receive_video_send_audio': 'Video received. Now, please send the audio file.',
        'start': 'Welcome! Please choose an option below:',
        'send_video': 'Please send a video file...',
        'download_video': 'Downloading the video, please wait...',
        'processing_video': 'Processing the video, please wait...',
        'send_audio': 'Please send an audio file.',
        'audio_received': 'Audio file received. Processing...',
        'video_received': 'Video file received. Now, please send an audio file.',
        'processing_done': 'Processing completed!',
        'file_sent': 'File sent successfully!',
        'not_video': 'Received file is not a video. Please send a video file.',
        'no_video_found': 'No video file found. Please start again by sending a video file.',
        'add_voice_success': 'Voice added to the video successfully!',
        'remove_voice_success': 'Voice removed from the video and file sent successfully!',
        'send_file_error': 'Error processing the file.',
        'clean_video_noice_success': 'The video has been cleaned of noise successfully!',
        'merged_audio_video': 'Audio cleaned successfully. Cleaned audio is being merged with video...',
        'extracting_video': 'Video file received. Extracting audio...',
        'extracting_audio_failed': 'Audio extraction failed. The audio file was not created.',
        'language_set': 'Language set to English!',
        'audio_cleaning': 'Audio extracted successfully. Audio cleaning...',
        'audio_received': "Audio file received. Cleaning noise...",
        'conversion_failed': "Failed to convert the audio to WAV format.",
        'processing_error': "An error occurred while processing the audio:",
        'cleaning_success': "Audio successfully cleaned. The cleaned file is saved as ",
        'no_audio_received': "No audio file received.",
        'cleaning_started': "Started cleaning the audio...",        
    }
}

language = 'en'

SAVE_DIR = 'downloads'
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
def clean_up_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

user_data = {}
async def set_language():
    pass

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Send me a video or audio file. You can use the following commands:\n"
        "/remove_voice_video - Remove voice from video\n"
        "/add_voice_video - Add voice to video\n"
        "/remove_add_voice_video - Remove voice and add new voice to video\n"
        "/clean_noise_audio - Clean noise from audio file\n"
        "/clean_noise_video - Clean noise from video file"
    )

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
def extract_rar(rar_path, extract_to):
    with rarfile.RarFile(rar_path, 'r') as rar_ref:
        rar_ref.extractall(extract_to)
async def handle_file(update: Update, context: CallbackContext):
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
        
        # العثور على أول ملف صوتي أو فيديو في الأرشيف
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
            await update.message.reply_text("No audio or video files found in the archive.")
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
            await update.message.reply_text("Unsupported file format.")
            os.remove(file_path)
            return

    await update.message.reply_text(f"File saved to {file_path}")
    pass

async def process_large_video(update: Update, context: CallbackContext):
    video_file = await update.message.video.get_file()
    file_info = await video_file.get_file()
    file_size = file_info.file_size

    size_limit = 100 * 1024 * 1024
    if file_size > size_limit:
        await update.message.reply_text("ملف الفيديو كبير جدًا. يرجى إرسال ملف أصغر.")
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

    # دمج الملفات المقسمة
    output_file_path = os.path.join(SAVE_DIR, 'merged_video.mp4')
    with open('filelist.txt', 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    command_merge = f"ffmpeg -f concat -safe 0 -i filelist.txt -c copy {output_file_path}"
    subprocess.call(command_merge, shell=True)

    # تنظيف الملفات المؤقتة
    for temp_file in temp_files:
        os.remove(temp_file)
    os.remove('filelist.txt')
    os.remove(video_file_path)

    await update.message.reply_text(f"تم معالجة الفيديو. تم حفظ الملف في {output_file_path}")
    await update.message.reply_document(document=open(output_file_path, 'rb'))

    # تنظيف مجلد التحميل
    clean_up_directory(SAVE_DIR)

async def handle_user_state(update: Update, context: CallbackContext):
    # Handle file based on state
    user_id = update.message.from_user.id
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
            await update.message.reply_text('Unknown state.')

async def remove_voice_from_video(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data[user_id] = {'state': 'waiting_for_video_to_remove_voice'}
    await update.message.reply_text(MESSAGES['en']['send_video'])
async def remove_voice_from_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == 'waiting_for_video_to_remove_voice':
        if update.message.video:
            await update.message.reply_text(MESSAGES['en']['download_video'])

            video_file = await update.message.video.get_file()
            video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')

            await video_file.download_to_drive(video_file_path)
            await update.message.reply_text('Processing the video, please wait...')

            output_file_path = video_file_path.replace('.mp4', '_no_voice.mp4')
            command = f"ffmpeg -i {video_file_path} -c:v copy -an {output_file_path}"
            subprocess.run(command, shell=True)

            if os.path.exists(output_file_path):
                await update.message.reply_document(document=open(output_file_path, 'rb'))
                await update.message.reply_text('Voice removed from video and file sent successfully!')
            else:
                await update.message.reply_text("Error processing the video.")
            
            clean_up_directory(SAVE_DIR)
            del user_data[user_id]  
        else:
            await update.message.reply_text('Received file is not a video. Please send a video file.')
    else:
        await update.message.reply_text('No video processing request found. Please use /remove_voice_from_video to start.')

async def add_voice_to_video(update: Update, context: CallbackContext):
    user_data[update.message.from_user.id] = {'state': 'waiting_for_video_to_add_voice'}
    await update.message.reply_text('Please send a video file.')
async def add_voice_to_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_video_to_add_voice":
        video_file = update.message.video
        file = await video_file.get_file()

        video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')  
        await file.download_to_drive(video_file_path)

        user_data[update.message.from_user.id] = {'video_file_path': video_file_path, 'state': 'waiting_for_audio_to_add_voice'}
        await update.message.reply_text(MESSAGES[language]['receive_video_send_audio'])
async def add_voice_to_video_process_audio(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_audio_to_add_voice":
        audio_file = await update.message.audio.get_file()
        audio_file_path = os.path.join(SAVE_DIR, f'{update.message.audio.file_unique_id}.mp3')
        await audio_file.download_to_drive(audio_file_path)

        user_info = user_data.get(update.message.from_user.id, {})
        video_file_path = user_info.get('video_file_path') 

        if video_file_path:
            output_file_path = video_file_path.replace('.mp4', '_with_new_voice.mp4')

            if not os.path.exists(video_file_path):
                await update.message.reply_text(f"Video file not found: {video_file_path}.")
                return

            await update.message.reply_text("Processing started. Adding the new voice to the video.")

            command_add_voice = (
            f"ffmpeg -i {video_file_path} -stream_loop -1 -i {audio_file_path} "
            f"-c:v copy -map 0:v:0 -map 1:a:0 -shortest {output_file_path}"
            )

            result = subprocess.run(command_add_voice, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print("Error adding voice:", result.stderr)
                return

            await update.message.reply_text('voice added to the video successfully !')

            if os.path.exists(output_file_path):
                await update.message.reply_text(f"Processing completed. Saved to {output_file_path}")
                await update.message.reply_document(document=open(output_file_path, 'rb'))
            else:
                await update.message.reply_text("Failed to create the new video file. Please check for errors.")

            clean_up_directory(SAVE_DIR)
            return
        else:
            await update.message.reply_text("No video file found. Please start again by sending a video file.")

async def remove_add_voice_to_video(update: Update, context: CallbackContext):
    user_data[update.message.from_user.id] = {'state': 'waiting_for_video_to_remove_add_voice'}
    await update.message.reply_text(MESSAGES[language]['send_video'])
async def remove_add_voice_to_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_video_to_remove_add_voice":
        video_file = update.message.video
        file_info = await video_file.get_file()
        file_size = file_info.file_size

        size_limit = 50 * 1024 * 1024  # 50 ميجابايت

        if file_size > size_limit:
            await process_large_video(update, context)
            return

        video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
        await video_file.download_to_drive(video_file_path)
        user_data[update.message.from_user.id] = {'video_file_path': video_file_path, 'state':'waiting_for_audio_to_remove_add_voice'}
        await update.message.reply_text(MESSAGES[language]['receive_video_send_audio'])
async def remove_add_voice_to_video_process_audio(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_audio_to_remove_add_voice":
        audio_file = await update.message.audio.get_file()
        audio_file_path = os.path.join(SAVE_DIR, f'{update.message.audio.file_unique_id}.mp3')
        await audio_file.download_to_drive(audio_file_path)

        user_info = user_data.get(update.message.from_user.id, {})
        video_file_path = user_info.get('video_file_path')

        if video_file_path:
            temp_no_voice_video_path = video_file_path.replace('.mp4', '_no_voice.mp4')
            temp_audio_path = "temp_audio.mp3"
            output_file_path = video_file_path.replace('.mp4', '_with_new_voice.mp4')

            await update.message.reply_text("Processing started. Removing the original voice from the video.")

            command_remove_voice = f"ffmpeg -i {video_file_path} -c:v copy -an {temp_no_voice_video_path}"
            subprocess.run(command_remove_voice, shell=True)

            # تصدير الصوت إلى ملف مؤقت
            audio_clip = AudioSegment.from_file(audio_file_path)
            audio_clip.export(temp_audio_path, format="mp3")

            await update.message.reply_text("Adding the new voice to the video.")

            # إضافة الصوت الجديد إلى الفيديو
            command_add_voice = (
                f"ffmpeg -i {temp_no_voice_video_path} -stream_loop -1 -i {temp_audio_path} "
                f"-c:v copy -map 0:v:0 -map 1:a:0 -shortest {output_file_path}")

            subprocess.run(command_add_voice, shell=True)

            # تنظيف الملفات المؤقتة
            os.remove(temp_no_voice_video_path)
            os.remove(temp_audio_path)
            os.remove(video_file_path)
            os.remove(audio_file_path)

            await update.message.reply_text(f"Processing completed. Saved to {output_file_path}")
            await update.message.reply_document(document=open(output_file_path, 'rb'))

            clean_up_directory(SAVE_DIR)
            return
        else:
            await update.message.reply_text("لم يتم العثور على ملف الفيديو. يرجى البدء من جديد بإرسال ملف الفيديو.")

async def clean_noise_from_audio(update: Update, context: CallbackContext):
    user_data[update.message.from_user.id] = {'state': 'waiting_for_audio_to_clean_noise'}
    await update.message.reply_text(MESSAGES[language]['send_audio'])
async def clean_noise_from_audio_process(update: Update, context: CallbackContext):

    user_id = update.message.from_user.id
    
    #
    language = user_data.get(user_id, {}).get('language', 'en')  
    
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_audio_to_clean_noise":
        if update.message.audio:
            try:
                # تحميل ملف الصوت
                audio_file = update.message.audio
                file = await audio_file.get_file()
                audio_file_path = os.path.join(SAVE_DIR, f'{audio_file.file_unique_id}.mp3')
                await file.download_to_drive(audio_file_path)
                await update.message.reply_text(MESSAGES[language]['audio_received'])

                # تحويل ملف الصوت إلى WAV
                temp_audio_path = "temp_audio.wav"
                command_convert_audio = f"ffmpeg -i \"{audio_file_path}\" {temp_audio_path}"
                await asyncio.create_subprocess_shell(command_convert_audio)

                if not os.path.exists(temp_audio_path):
                    await update.message.reply_text(MESSAGES[language]['conversion_failed'])
                    return

                # استخدام Spleeter لفصل الصوت البشري عن الموسيقى
                separator = Separator('spleeter:2stems')  # استخدام نموذج فصل المسارين (vocals و accompaniment)
                spleeter_output_dir = os.path.join(SAVE_DIR, 'spleeter_output')
                separator.separate_to_file(temp_audio_path, spleeter_output_dir)

                # مسارات الملفات المفصولة
                vocals_path = os.path.join(spleeter_output_dir, 'vocals.wav')
                accompaniment_path = os.path.join(spleeter_output_dir, 'accompaniment.wav')

                # تنقية الصوت البشري باستخدام noisereduce
                with wave.open(vocals_path, 'rb') as wf:
                    rate = wf.getframerate()
                    channels = wf.getnchannels()
                    width = wf.getsampwidth()
                    chunk_size = 1024 * 1024  # حجم الدفعة
                    data = wf.readframes(chunk_size)
                    cleaned_data = []

                    while data:
                        # تنقية الضوضاء من الصوت
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        cleaned_chunk = nr.reduce_noise(y=audio_array, sr=rate)
                        cleaned_data.append(cleaned_chunk)
                        data = wf.readframes(chunk_size)

                    cleaned_audio = np.concatenate(cleaned_data)
                    cleaned_vocals_path = vocals_path.replace('.wav', '_cleaned.wav')

                    # حفظ الصوت النظيف
                    with wave.open(cleaned_vocals_path, 'wb') as cleaned_wf:
                        cleaned_wf.setnchannels(channels)
                        cleaned_wf.setsampwidth(width)
                        cleaned_wf.setframerate(rate)
                        cleaned_wf.writeframes(cleaned_audio.tobytes())

                # تحويل الصوت النظيف إلى MP3
                output_file_path = audio_file_path.replace('.mp3', '_cleaned.mp3')
                command_convert_cleaned_audio = f"ffmpeg -i \"{cleaned_vocals_path}\" {output_file_path}"
                await asyncio.create_subprocess_shell(command_convert_cleaned_audio)

                # حذف الملفات المؤقتة
                os.remove(temp_audio_path)
                os.remove(cleaned_vocals_path)

                await update.message.reply_text(f"{MESSAGES[language]['cleaning_success']} {output_file_path}")
                await update.message.reply_document(document=open(output_file_path, 'rb'))

            except Exception as e:
                await update.message.reply_text(f"{MESSAGES[language]['processing_error']} {str(e)}")
        else:
            await update.message.reply_text(MESSAGES[language]['no_audio_received'])
        
        clean_up_directory(SAVE_DIR)

async def clean_noise_from_video(update: Update, context: CallbackContext):
    user_data[update.message.from_user.id] = {'state': 'waiting_for_video_to_clean_noise'}
    await update.message.reply_text(MESSAGES[language]['send_video'])
async def clean_noise_from_video_process(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['state'] == "waiting_for_video_to_clean_noise":
        if update.message.video:
            try:
                video_file = await update.message.video.get_file()
                video_file_path = os.path.join(SAVE_DIR, f'{update.message.video.file_unique_id}.mp4')
                await video_file.download_to_drive(video_file_path)

                await update.message.reply_text(MESSAGES[language]['extracting_video'])

                temp_audio_path = "temp_audio.wav"
                output_file_path = video_file_path.replace('.mp4', '_cleaned.mp4')

                # Extract audio asynchronously using ffmpeg
                command_extract_audio = f"ffmpeg -i \"{video_file_path}\" -q:a 0 -map a {temp_audio_path}"
                await asyncio.create_subprocess_shell(command_extract_audio)

                if not os.path.exists(temp_audio_path):
                    await update.message.reply_text(MESSAGES[language]['extracting_audio_failed'])
                    return

                await update.message.reply_text(MESSAGES[language]['audio_cleaning'])

                # Step 1: Use Spleeter to separate vocals and accompaniment
                separator = Separator('spleeter:2stems')  # Two stems model: vocals and accompaniment
                spleeter_output_dir = os.path.join(SAVE_DIR, 'spleeter_output')
                separator.separate_to_file(temp_audio_path, spleeter_output_dir)

                # Spleeter output paths
                vocals_path = os.path.join(spleeter_output_dir, 'vocals.wav')
                accompaniment_path = os.path.join(spleeter_output_dir, 'accompaniment.wav')

                # Step 2: Clean vocals using noisereduce
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

                await update.message.reply_text(MESSAGES[language]['merged_audio_video'])

                # Step 3: Merge cleaned vocals with original video
                command_add_cleaned_audio = f"ffmpeg -i \"{video_file_path}\" -i \"{cleaned_vocals_path}\" -c:v copy -map 0:v:0 -map 1:a:0 {output_file_path}"
                await asyncio.create_subprocess_shell(command_add_cleaned_audio)

                # Clean up temporary files
                os.remove(temp_audio_path)
                os.remove(cleaned_vocals_path)

                await update.message.reply_text(MESSAGES[language]['clean_video_noice_success'])
                await update.message.reply_document(document=open(output_file_path, 'rb'))

            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")
        else:
            await update.message.reply_text(MESSAGES[language]['no_video_found'])

        clean_up_directory()

async def handle_non_command_message(update: Update, context: CallbackContext):
    if update.message.text and not update.message.text.startswith('/'):
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

    # Message handlers
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_command_message))

    application.add_handler(MessageHandler(filters.VIDEO, handle_user_state))
    application.add_handler(MessageHandler(filters.AUDIO, handle_user_state))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()