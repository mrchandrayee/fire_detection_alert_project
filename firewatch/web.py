import time,cv2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse,StreamingResponse
from .config import load_config
from .engine import FireDetectionEngine
app=FastAPI(title="Fire Detection & Alert")
engine=None
PAGE='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire Detection & Alert</title>
<style>body{margin:0;background:#0b1220;color:#e8eef9;font:15px Arial}header{padding:18px 24px;background:#111c30;display:flex;justify-content:space-between}main{padding:20px;display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,1fr);gap:18px}.card{background:#142139;border:1px solid #263957;border-radius:12px;padding:16px}.feed{width:100%;border-radius:8px;background:#05080e;min-height:250px;object-fit:contain}.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.num{font-size:28px;font-weight:bold;margin-top:8px}.muted{color:#9eb0ca}.event{padding:10px 0;border-bottom:1px solid #293b58}button{background:#d83b3b;color:white;border:0;padding:8px 12px;border-radius:7px}@media(max-width:800px){main{grid-template-columns:1fr}}</style></head>
<body><header><b>🔥 Fire Detection &amp; Alert</b><span id="state">Connecting…</span></header><main>
<section class="card"><h3>Live Camera Feed</h3><img class="feed" src="/video_feed"><p class="muted">Annotated camera stream · refreshes automatically</p></section>
<aside><div class="card"><h3>Pipeline Status</h3><div class="stats"><div><span class="muted">Camera</span><div class="num" id="connected">—</div></div><div><span class="muted">FPS</span><div class="num" id="fps">0</div></div><div><span class="muted">Frames</span><div class="num" id="frames">0</div></div><div><span class="muted">Events</span><div class="num" id="count">0</div></div></div><p class="muted" id="error"></p></div>
<div class="card" style="margin-top:16px"><h3>Recent Fire / Smoke Events</h3><div id="events">Waiting for events…</div></div></aside></main>
<script>async function refresh(){try{let s=await(await fetch('/api/status')).json();document.getElementById('state').textContent=s.state;document.getElementById('connected').textContent=s.connected?'ONLINE':'OFFLINE';document.getElementById('fps').textContent=s.fps;document.getElementById('frames').textContent=s.frames;document.getElementById('count').textContent=s.event_count;document.getElementById('error').textContent=s.last_error||'';let e=await(await fetch('/api/events?limit=12')).json();document.getElementById('events').innerHTML=e.length?e.map(x=>`<div class="event"><b>${x.event_type.toUpperCase()}</b> · ${(x.confidence*100).toFixed(1)}%<br><small class="muted">${new Date(x.timestamp*1000).toLocaleString()}</small></div>`).join(''):'No events yet';}catch(e){document.getElementById('state').textContent='API unavailable'}}setInterval(refresh,2000);refresh();</script></body></html>'''
@app.get("/",response_class=HTMLResponse)
def home(): return PAGE
@app.get("/api/health")
def health(): return {"ok":True}
@app.get("/api/status")
def status(): return engine.get_status() if engine else {"state":"not_started"}
@app.get("/api/events")
def events(limit:int=50): return engine.store.recent(max(1,min(limit,200))) if engine else []
def frames():
    while True:
        frame=engine.get_frame() if engine else None
        if frame is None: time.sleep(.1); continue
        ok,buf=cv2.imencode(".jpg",frame)
        if ok: yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"+buf.tobytes()+b"\r\n"
        time.sleep(.04)
@app.get("/video_feed")
def video_feed(): return StreamingResponse(frames(),media_type="multipart/x-mixed-replace; boundary=frame")
def create_app(cfg,source):
    global engine
    engine=FireDetectionEngine(cfg,source); engine.start()
    return app
