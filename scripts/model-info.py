import json,urllib.request
r=json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:11434/api/show',data=json.dumps({'model':'qwen3-vl:4b-instruct'}).encode(),headers={'content-type':'application/json'})));print({k:r.get(k) for k in ['capabilities','details','parameters']});print(r.get('template','')[-1000:])
