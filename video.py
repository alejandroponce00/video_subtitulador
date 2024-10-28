import os
import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import pysrt
from googletrans import Translator

def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

def translate_text(text, dest_language='es'):
    translator = Translator()
    return translator.translate(text, dest=dest_language).text

def create_subtitles(transcript, duration, subtitle_file, dest_language='es'):
    subs = pysrt.SubRipFile()
    words = transcript.split()
    chars_per_second = 15
    chars_per_line = 60
    current_line = ""
    start_time = 0

    for word in words:
        if len(current_line) + len(word) + 1 > chars_per_line:
            end_time = start_time + (len(current_line) / chars_per_second)
            translated_line = translate_text(current_line.strip(), dest_language)
            sub = pysrt.SubRipItem(index=len(subs) + 1, 
                                   start=pysrt.SubRipTime(seconds=start_time), 
                                   end=pysrt.SubRipTime(seconds=end_time), 
                                   text=translated_line)
            subs.append(sub)
            start_time = end_time
            current_line = word + " "
        else:
            current_line += word + " "

    if current_line:
        end_time = min(start_time + (len(current_line) / chars_per_second), duration)
        translated_line = translate_text(current_line.strip(), dest_language)
        sub = pysrt.SubRipItem(index=len(subs) + 1, 
                               start=pysrt.SubRipTime(seconds=start_time), 
                               end=pysrt.SubRipTime(seconds=end_time), 
                               text=translated_line)
        subs.append(sub)

    subs.save(subtitle_file, encoding='utf-8')

def add_subtitles_to_video(video_path, subtitle_file, output_path):
    video = VideoFileClip(video_path)
    subtitles = pysrt.open(subtitle_file)

    def create_subtitle_clips(subtitle):
        start_time = subtitle.start.ordinal / 1000
        end_time = subtitle.end.ordinal / 1000
        video_width, video_height = video.size

        text_clip = TextClip(subtitle.text, fontsize=24, color='white', bg_color='black',
                             size=(video_width, None), method='caption').set_position(('center', 'bottom'))
        text_clip = text_clip.set_start(start_time).set_end(end_time)
        return text_clip

    subtitle_clips = [create_subtitle_clips(subtitle) for subtitle in subtitles]

    final_video = CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_path)

def main():
    # Crear la carpeta de salida si no existe
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Solicitar al usuario la ruta del video
    video_path = input("Por favor, ingrese la ruta del video: ")

    # Extraer el audio del video
    video = VideoFileClip(video_path)
    audio_path = os.path.join(output_folder, "temp_audio.wav")
    video.audio.write_audiofile(audio_path)

    # Transcribir el audio
    transcript = transcribe_audio(audio_path)

    # Crear archivo de subtítulos en español
    subtitle_file = os.path.join(output_folder, "subtitles_es.srt")
    create_subtitles(transcript, video.duration, subtitle_file, dest_language='es')

    # Añadir subtítulos al video
    output_video_path = os.path.join(output_folder, "video_con_subtitulos_es.mp4")
    add_subtitles_to_video(video_path, subtitle_file, output_video_path)

    # Limpiar archivos temporales
    os.remove(audio_path)

    print(f"Video con subtítulos en español guardado en: {output_video_path}")

if __name__ == "__main__":
    main()