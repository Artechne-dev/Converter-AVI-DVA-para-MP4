import subprocess
import threading
import os
import shutil

class VideoConverter:
    def __init__(self):
        self._check_ffmpeg()
        self.current_process = None

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

    def convert(self, input_path: str, output_path: str, progress_callback=None, completion_callback=None, error_callback=None, encoder_callback=None, ultra_fast=False):
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
                best_encoder = "libx264"
                encoders_to_test = {
                    "h264_nvenc": "NVIDIA",
                    "h264_qsv": "Intel",
                    "h264_amf": "AMD"
                }
                
                use_copy = False
                if ultra_fast:
                    if encoder_callback:
                        encoder_callback("Testando cópia direta (Ultra Rápida)...")
                    
                    test_command = [
                        self.ffmpeg_path,
                        "-nostdin",
                        "-y",
                        "-i", input_path,
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-t", "0.5",
                        "-f", "null",
                        "-"
                    ]
                    try:
                        test_process = subprocess.Popen(
                            test_command,
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        test_process.communicate()
                        if test_process.returncode == 0:
                            use_copy = True
                    except Exception:
                        pass
                
                if use_copy:
                    best_encoder = "copy"
                    encoder_name = "Cópia Direta"
                else:
                    if encoder_callback:
                        encoder_callback("Detectando aceleradores...")
                    
                    for enc, name in encoders_to_test.items():
                        test_command = [
                            self.ffmpeg_path,
                            "-nostdin",
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
                                stdin=subprocess.DEVNULL,
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
                    if best_encoder == "copy":
                        encoder_callback("Usando Cópia Direta (Ultra Rápida)...")
                    else:
                        encoder_callback(f"Usando {encoder_name} ({best_encoder})...")
                
                command = [
                    self.ffmpeg_path,
                    "-nostdin",
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
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                self.current_process = process
                
                import re
                import time
                
                total_seconds = None
                start_time = time.time()
                stderr_buffer = []
                
                for line in iter(process.stderr.readline, ''):
                    stderr_buffer.append(line)
                    
                    if total_seconds is None:
                        dur_match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                        if dur_match:
                            hh, mm, ss, ms = map(int, dur_match.groups())
                            total_seconds = hh * 3600 + mm * 60 + ss + ms / 100.0
                    
                    prog_match = re.search(r"time=\s*(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                    if prog_match and total_seconds:
                        hh, mm, ss, ms = map(int, prog_match.groups())
                        current_seconds = hh * 3600 + mm * 60 + ss + ms / 100.0
                        
                        percent = min(100.0, (current_seconds / total_seconds) * 100.0)
                        elapsed = time.time() - start_time
                        if current_seconds > 0:
                            eta = max(0.0, (elapsed / current_seconds) * (total_seconds - current_seconds))
                            eta_min = int(eta // 60)
                            eta_sec = int(eta % 60)
                            eta_str = f"{eta_min:02d}:{eta_sec:02d}"
                            
                            if progress_callback:
                                progress_callback(f"{percent:.1f}% (Restam {eta_str})")
                                
                process.wait()
                self.current_process = None
                
                if process.returncode != 0:
                    if error_callback:
                        err_text = "".join(stderr_buffer)
                        error_callback(f"Erro na conversão ({best_encoder}): {err_text}")
                    return

                if completion_callback:
                    completion_callback()
            except Exception as e:
                if error_callback:
                    error_callback(str(e))

        thread = threading.Thread(target=_run)
        thread.start()

    def cancel(self):
        if self.current_process:
            try:
                self.current_process.kill()
            except Exception:
                pass
            self.current_process = None
