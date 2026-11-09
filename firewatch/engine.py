import cv2,time,threading
from .detector import FireSmokeDetector
from .store import EventStore
from .telegram import TelegramAlerter
from .publisher import RTSPPublisher
class FireDetectionEngine:
    def __init__(self,cfg,source):
        self.cfg=cfg; self.source=source; self.camera="camera-01"
        self.detector=FireSmokeDetector(cfg.get("detector",{}))
        ev=cfg.get("events",{})
        self.store=EventStore(ev.get("database","runs/events.db"),ev.get("snapshot_dir","runs/events"))
        self.alerter=TelegramAlerter(cfg.get("telegram",{}))
        self.cooldown=float(ev.get("cooldown_seconds",30)); self.last={}
        self.lock=threading.RLock(); self.frame=None; self.running=False
        self.status={"connected":False,"state":"starting","frames":0,"fps":0.0,"last_error":None,"event_count":0}
        self.thread=None; self.cap=None; self.publisher=None
    def start(self):
        self.running=True; self.thread=threading.Thread(target=self._loop,daemon=True); self.thread.start()
    def stop(self):
        self.running=False
        if self.thread: self.thread.join(timeout=4)
        if self.cap: self.cap.release()
        if self.publisher: self.publisher.close()
    def _loop(self):
        cam=self.cfg.get("camera",{})
        src=self.source
        if isinstance(src,str) and src.isdigit(): src=int(src)
        while self.running:
            self.cap=cv2.VideoCapture(src)
            if not self.cap.isOpened():
                self.status.update(connected=False,state="reconnecting",last_error="Unable to open video source")
                time.sleep(float(cam.get("reconnect_seconds",3))); continue
            self.status.update(connected=True,state="running",last_error=None)
            fps_count=0; fps_start=time.time()
            while self.running:
                ok,frame=self.cap.read()
                if not ok: break
                try:
                    detections=self.detector.detect(frame)
                    annotated=frame.copy()
                    for d in detections:
                        x1,y1,x2,y2=d["box"]; color=(0,0,255) if d["event_type"]=="fire" else (255,180,0)
                        cv2.rectangle(annotated,(x1,y1),(x2,y2),color,2)
                        cv2.putText(annotated,f'{d["label"]} {d["confidence"]:.2f}',(x1,max(20,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.65,color,2)
                        key=d["event_type"]; now=time.time()
                        if now-self.last.get(key,0)>=self.cooldown:
                            event=self.store.add(self.camera,key,d["label"],d["confidence"],d["track_id"],frame)
                            self.last[key]=now; self.status["event_count"]=self.store.count()
                            message=f'{key.upper()} DETECTED | camera={self.camera} | confidence={d["confidence"]:.2f}'
                            print("[EVENT]",message); self.alerter.send(message,event["snapshot"])
                    if self.publisher is None:
                        h,w=annotated.shape[:2]
                        self.publisher=RTSPPublisher(self.cfg.get("stream",{}),w,h)
                    self.publisher.write(annotated)
                    with self.lock: self.frame=annotated
                    self.status["frames"]+=1; fps_count+=1
                    if time.time()-fps_start>=2:
                        self.status["fps"]=round(fps_count/(time.time()-fps_start),1)
                        fps_count=0; fps_start=time.time()
                except Exception as e:
                    self.status["last_error"]=str(e); print("[pipeline]",e)
            self.cap.release(); self.cap=None
            if self.running:
                self.status.update(connected=False,state="reconnecting")
                time.sleep(float(cam.get("reconnect_seconds",3)))
        self.status["state"]="stopped"
    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()
    def get_status(self):
        return {**self.status,"event_count":self.store.count(),"source":str(self.source)}
