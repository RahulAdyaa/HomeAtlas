import urllib.request,json
r=json.load(urllib.request.urlopen('http://127.0.0.1:11434/api/tags'))
for model in r['models']:
 if model['name']=='qwen3-vl:4b-instruct':print(json.dumps({'name':model['name'],'digest':model['digest'],'size':model['size'],'details':model['details']}))
