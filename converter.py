import subprocess
import threading
import os
import shutil

class VideoConverter:
    def __init__(self):
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        import sys
        
        # Check system PATH
        if shutil.which("ffmpeg"):
            self.ffmpeg_path = "ffmpeg"
            self.has_ffmpeg = True
            return
            
        # Check local folder
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        local_ffmpeg = os.path.join(base_dir, "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            self.ffmpeg_path = local_ffmpeg
            self.has_ffmpeg = True
        else:
            self.ffmpeg_path = None
            self.has_ffmpeg = False

    @staticmethod
    def download_ffmpeg(progress_callback=None, completion_callback=None, error_callback=None):
        def _run():
            try:
                import urllib.request
                import zipfile
                import io
                import sys
                
                url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                
                if progress_callback:
                    progress_callback("Baixando FFmpeg (Isso pode demorar)...")

                response = urllib.request.urlopen(url)
                
                if progress_callback:
                    progress_callback("Extraindo FFmpeg...")

                with zipfile.ZipFile(io.BytesIO(response.read())) as zip_ref:
                    for file_info in zip_ref.infolist():
                        if file_info.filename.endswith('ffmpeg.exe'):
                            file_info.filename = 'ffmpeg.exe'
                            
                            if getattr(sys, 'frozen', False):
                                save_dir = os.path.dirname(sys.executable)
                            else:
                                save_dir = os.path.dirname(os.path.abspath(__file__))
                                
                            zip_ref.extract(file_info, save_dir)
                            break
                            
                if completion_callback:
                    completion_callback()
            except Exception as e:
                if error_callback:
                    error_callback(str(e))
                    
        thread = threading.Thread(target=_run)
        thread.start()

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
