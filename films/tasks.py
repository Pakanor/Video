from celery import shared_task
import os
import subprocess
import logging
from django.conf import settings
from .models import Film
import re
import time
from django.db import models
logger = logging.getLogger(__name__)


@shared_task(bind=True)
def convert_to_hls_task(self, film_id):
    """ Konwersja MP4 do HLS w Celery z monitorowaniem czasu pozostałego """
    try:
        # Inicjalizacja
        film = Film.objects.get(id=film_id)
        if not film.link:
            raise ValueError("Brak pliku w bazie danych!")
        if film.hls_playlist:
            logger.info(
                f"Film {film_id} już został skonwertowany. Pomijam konwersję.")
            return film.hls_playlist

        input_file = os.path.join(settings.MEDIA_ROOT, str(film.link))
        output_dir = os.path.join(
            settings.MEDIA_ROOT, "videos", "hls", str(film.id))
        os.makedirs(output_dir, exist_ok=True)
        output_playlist = os.path.join(output_dir, "output.m3u8")

        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Plik nie istnieje: {input_file}")

        # Uruchomienie FFmpeg
        logger.info(f"🎬 Konwertuję: {input_file} ➝ {output_playlist}")

        # Komenda do FFmpeg
        command = [
            "ffmpeg",
            "-i", input_file,
            "-preset", "fast",  # Dodaj opcje konwersji
            "-c:v", "libx264",
            "-c:a", "aac",
            "-f", "hls",
            "-start_number", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            output_playlist
        ]

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Monitorowanie postępu
        total_duration = None
        current_duration = 0

        while True:
            # Pobieranie stanu z wyjścia ffmpeg
            stderr = process.stderr.read()
            remaining_time = extract_remaining_time(stderr)

            if remaining_time:
                remaining_minutes, remaining_seconds = map(
                    int, remaining_time.split(":"))
                logger.info(
                    f"⏳ Pozostały czas: {remaining_minutes}:{remaining_seconds}")

            if process.poll() is not None:
                break

        # Zakończenie konwersji
        film.hls_playlist = film.hls_playlist = f"{settings.MEDIA_URL}videos/hls/{film.id}/output.m3u8"

        film.is_converted = True
        film.save()

        logger.info(f"✅ Konwersja zakończona: {film.hls_playlist}")
        return film.hls_playlist

    except Film.DoesNotExist:
        logger.error(f"❌ Film o ID {film_id} nie istnieje!")
        return None
    except FileNotFoundError as e:
        logger.error(f"❌ Plik nie znaleziony: {e}")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Błąd FFmpeg: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Błąd konwersji: {e}")
        return None


def extract_remaining_time(stderr):
    """ Ekstrakcja pozostałego czasu z stderr ffmpeg """
    match = re.search(r'(\d{2}):(\d{2}):(\d{2})', stderr)
    if match:
        return f"{match.group(2)}:{match.group(3)}"
    return None
