class FireSmokeDetector:
    def __init__(self,cfg):
        self.backend=cfg.get("backend","none")
        self.conf=float(cfg.get("confidence",.45))
        self.fire={str(x).lower() for x in cfg.get("fire_labels",["fire"])}
        self.smoke={str(x).lower() for x in cfg.get("smoke_labels",["smoke"])}
        self.model=None
        if self.backend=="yolo":
            from ultralytics import YOLO
            weights=cfg.get("weights")
            if not weights: raise ValueError("detector.weights is required for YOLO backend")
            self.model=YOLO(weights)
        elif self.backend!="none":
            raise ValueError("detector.backend must be yolo or none")
    def detect(self,frame):
        if self.backend=="none": return []
        result=self.model.predict(frame,conf=self.conf,imgsz=int(640),verbose=False)[0]
        found=[]
        if result.boxes is None: return found
        for b in result.boxes:
            cls_id=int(b.cls[0]); label=str(result.names.get(cls_id,cls_id)).lower()
            if label not in self.fire and label not in self.smoke: continue
            x1,y1,x2,y2=[int(v) for v in b.xyxy[0].tolist()]
            found.append({"box":[x1,y1,x2,y2],"label":label,
                          "confidence":float(b.conf[0]),"track_id":-1,
                          "event_type":"fire" if label in self.fire else "smoke"})
        return found
