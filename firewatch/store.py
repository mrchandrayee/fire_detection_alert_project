import sqlite3, time
from pathlib import Path
import cv2
class EventStore:
    def __init__(self,db_path,snapshot_dir):
        self.db=Path(db_path); self.db.parent.mkdir(parents=True,exist_ok=True)
        self.images=Path(snapshot_dir); self.images.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.db) as c:
            c.execute('''CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL NOT NULL,
                camera TEXT, event_type TEXT, label TEXT, confidence REAL,
                track_id INTEGER, snapshot TEXT)''')
    def add(self,camera,event_type,label,confidence,track_id,frame):
        ts=time.time(); path=self.images/f"{int(ts*1000)}_{event_type}_{track_id}.jpg"
        cv2.imwrite(str(path),frame)
        with sqlite3.connect(self.db) as c:
            cur=c.execute("INSERT INTO events(timestamp,camera,event_type,label,confidence,track_id,snapshot) VALUES(?,?,?,?,?,?,?)",
                (ts,camera,event_type,label,float(confidence),int(track_id),str(path)))
            eid=cur.lastrowid
        return {"id":eid,"timestamp":ts,"camera":camera,"event_type":event_type,
                "label":label,"confidence":float(confidence),"track_id":int(track_id),"snapshot":str(path)}
    def recent(self,limit=50):
        with sqlite3.connect(self.db) as c:
            c.row_factory=sqlite3.Row
            rows=c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?",(int(limit),)).fetchall()
        return [dict(r) for r in rows]
    def count(self):
        with sqlite3.connect(self.db) as c: return c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
