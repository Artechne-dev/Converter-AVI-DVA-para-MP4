import subprocess
import threading
import os
import shutil

class VideoConverter:
    def __init__(self):
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        import sys
        
        # Check PyInstaller temporary directory (sys._MEIPASS)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            temp_ffmpeg = os.path.join(sys._MEIPASS, "ffmpeg.exe")
            if os.path.exists(temp_ffmpeg):
                self.ffmpeg_path = temp_ffmpeg
                self.has_ffmpeg = True
                return
        
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

    def convert(self, input_path: str, output_path: str, progress_callback=None, completion_callback=None, error_callback=None, encoder_callback=None):
        if input_path.lower().endswith(".mp4") and output_path.lower().endswith(".mp4"):
            if error_callback:
                error_callback("Arquivo de origem já é MP4. Conversão bloqueada.")
            return

        if os.path.abspath(input_path) == os.path.abspath(output_path):
            if error_callback:
                error_callback("Arquivo de origem e destino não podem ser iguais.")
            return

        def _run():
            try:
                if encoder_callback:
                    encoder_callback("Detectando aceleradores...")
                
                best_encoder = "libx264"
                encoders_to_test = {
                    "h264_nvenc": "NVIDIA",
                    "h264_qsv": "Intel",
                    "h264_amf": "AMD"
                }
                
                for enc, name in encoders_to_test.items():
                    test_command = [
                        self.ffmpeg_path,
                        "-y",
                        "-f", "lavfi",
                        "-i", "color=c=black:s=64x64:d=0.1",
                        "-c:v", enc,
                        "-f", "null",
                        "-"
                    ]
                    try:
                        test_process = subprocess.Popen(
                            test_command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        test_process.communicate()
                        if test_process.returncode == 0:
                            best_encoder = enc
                            break
                    except Exception:
                        pass
                
                encoder_name = encoders_to_test.get(best_encoder, "CPU")
                if encoder_callback:
                    encoder_callback(f"Usando {encoder_name} ({best_encoder})...")
                
                command = [
                    self.ffmpeg_path,
                    "-y",
                    "-i", input_path,
                    "-c:v", best_encoder,
                ]
                
                if best_encoder == "libx264":
                    command.extend(["-preset", "fast"])
                
                command.extend([
                    "-c:a", "aac",
                    output_path
                ])
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    if error_callback:
                        error_callback(f"Erro na conversão ({best_encoder}): {stderr.decode('utf-8', errors='ignore')}")
                    return

                if completion_callback:
                    completion_callback()
            except Exception as e:
                if error_callback:
                    error_callback(str(e))

        thread = threading.Thread(target=_run)
        thread.start()
