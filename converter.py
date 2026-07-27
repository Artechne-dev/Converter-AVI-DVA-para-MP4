import subprocess
import threading
import os
import shutil

class VideoConverter:
    def __init__(self):
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        self.ffmpeg_path = "ffmpeg"
        if not shutil.which("ffmpeg"):
            raise FileNotFoundError("FFmpeg não encontrado no sistema.\nPara que o conversor funcione, instale o FFmpeg e adicione-o ao PATH.\nDownload: https://ffmpeg.org/download.html")

    def convert(self, input_path: str, output_path: str, progress_callback=None, completion_callback=None, error_callback=None):
        def _run():
            try:
                command = [
                    self.ffmpeg_path,
                    "-y",
                    "-i", input_path,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-c:a", "aac",
                    output_path
                ]
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    if error_callback:
                        error_callback(f"Erro na conversão: {stderr.decode('utf-8', errors='ignore')}")
                    return

                if completion_callback:
                    completion_callback()
            except Exception as e:
                if error_callback:
                    error_callback(str(e))

        thread = threading.Thread(target=_run)
        thread.start()
