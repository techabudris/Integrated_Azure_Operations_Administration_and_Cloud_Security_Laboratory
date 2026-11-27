#!/usr/bin/env python3
"""Real localhost HTTP service for CCSE-102 Linux operations practice.
Run in an isolated lab only. Never bind to public interfaces.
"""
import argparse, json, datetime as dt
from http.server import BaseHTTPRequestHandler, HTTPServer
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ('/health','/metrics'):
            self.send_response(404); self.end_headers(); return
        payload={'status':'healthy','system':'CCSE-102 local Linux service','time':dt.datetime.now(dt.timezone.utc).isoformat()} if self.path=='/health' else {'cpu_percent':24,'requests_total':13,'notice':'synthetic demonstration metrics'}
        body=json.dumps(payload).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8088); a=p.parse_args()
    if not 1024<=a.port<=65535: raise SystemExit('Choose a non-privileged port')
    server=HTTPServer(('127.0.0.1',a.port),Handler)
    print('Local only at http://127.0.0.1:'+str(a.port)+'/health',flush=True)
    server.serve_forever()
