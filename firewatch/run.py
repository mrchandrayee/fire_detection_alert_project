import argparse,uvicorn
from .config import load_config
from .web import create_app
def main():
    p=argparse.ArgumentParser(description="Fire detection and alert dashboard")
    p.add_argument("--config",default="config.yaml"); p.add_argument("--source",default=None)
    a=p.parse_args(); cfg=load_config(a.config)
    source=a.source if a.source is not None else cfg.get("camera",{}).get("source","0")
    web=cfg.get("app",{})
    create_app(cfg,source)
    uvicorn.run("firewatch.web:app",host=web.get("host","127.0.0.1"),port=int(web.get("port",8000)),reload=False)
if __name__=="__main__": main()
