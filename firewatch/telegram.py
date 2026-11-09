import os,time,requests
class TelegramAlerter:
    def __init__(self,cfg):
        self.enabled=bool(cfg.get("enabled",False)); self.photo=bool(cfg.get("send_photo",True))
        self.token=os.getenv("TELEGRAM_BOT_TOKEN"); self.chat=os.getenv("TELEGRAM_CHAT_ID")
        self.cooldown=float(cfg.get("cooldown_seconds",30)); self.last={}
    def send(self,message,image_path=None):
        if not self.enabled: return
        if not self.token or not self.chat:
            print("[telegram] enabled but TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing"); return
        now=time.time(); key=message.split("|")[0]
        if now-self.last.get(key,0)<self.cooldown: return
        base=f"https://api.telegram.org/bot{self.token}/"
        try:
            if image_path and self.photo:
                with open(image_path,"rb") as f:
                    r=requests.post(base+"sendPhoto",data={"chat_id":self.chat,"caption":message},
                                    files={"photo":f},timeout=25)
            else:
                r=requests.post(base+"sendMessage",data={"chat_id":self.chat,"text":message},timeout=25)
            r.raise_for_status(); self.last[key]=now
        except requests.RequestException as e: print("[telegram] send failed:",e)
