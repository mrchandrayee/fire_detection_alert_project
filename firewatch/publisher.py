import subprocess
class RTSPPublisher:
    def __init__(self,cfg,width,height):
        self.proc=None; self.url=cfg.get("publish_url","")
        if not self.url: return
        cmd=[cfg.get("ffmpeg","ffmpeg"),"-loglevel","error","-re","-f","rawvideo",
             "-pix_fmt","bgr24","-s",f"{width}x{height}","-r",str(cfg.get("fps",20)),
             "-i","-","-an","-c:v","libx264","-preset","veryfast","-tune","zerolatency",
             "-b:v",cfg.get("bitrate","1500k"),"-f","rtsp","-rtsp_transport","tcp",self.url]
        try: self.proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        except (FileNotFoundError,OSError) as e: print("[publisher] FFmpeg unavailable:",e)
    def write(self,frame):
        if self.proc and self.proc.poll() is None:
            try: self.proc.stdin.write(frame.tobytes())
            except (BrokenPipeError,OSError): self.close()
    def close(self):
        if self.proc:
            try:
                if self.proc.stdin: self.proc.stdin.close()
                self.proc.terminate(); self.proc.wait(timeout=3)
            except Exception:
                try: self.proc.kill()
                except Exception: pass
            self.proc=None
