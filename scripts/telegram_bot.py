#!/usr/bin/env python3
"""Long-polling Telegram commands: /start, /latest, /top, /digest. No third-party packages."""
import json, os, time, urllib.parse, urllib.request
from pathlib import Path
TOKEN=os.getenv('TELEGRAM_BOT_TOKEN','').strip()
NEWS_URL=os.getenv('AZEROTH_NEWS_URL','').strip()
LOCAL_NEWS=Path(__file__).resolve().parents[1]/'data'/'news.json'
if not TOKEN: raise SystemExit('Set TELEGRAM_BOT_TOKEN in your environment first.')
API='https://api.telegram.org/bot'+TOKEN+'/'
def api(method,payload=None):
    req=urllib.request.Request(API+method,data=json.dumps(payload or {}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=35) as r:body=json.loads(r.read())
    if not body.get('ok'):raise RuntimeError(body.get('description','Telegram API error'))
    return body['result']
def load_items():
    try:
        if NEWS_URL:
            req=urllib.request.Request(NEWS_URL,headers={'User-Agent':'AzerothPulseBot/1.0'})
            with urllib.request.urlopen(req,timeout=20) as r:data=json.loads(r.read())
        else:data=json.loads(LOCAL_NEWS.read_text(encoding='utf-8'))
        return data if isinstance(data,list) else data.get('items',[])
    except Exception as e:print('Could not read news:',e);return []
def send(chat,text,keyboard=None):
    p={'chat_id':chat,'text':text,'disable_web_page_preview':False}
    if keyboard:p['reply_markup']={'inline_keyboard':keyboard}
    try:api('sendMessage',p)
    except Exception as e:print('sendMessage failed:',e)
def list_message(items,title):
    if not items:return 'Свежих публикаций пока нет. Загляни позже — лента обновляется автоматически.',None
    lines=[title,''];buttons=[]
    for i,x in enumerate(items,1):
        lines.append(f"{i}. {x.get('title_ru') or x.get('title','Новость WoW')}\n⚡ Хайп: {x.get('heat_score',0)}/100\n{x.get('url','')}\n")
        buttons.append([{'text':f'Открыть новость {i} ↗','url':x.get('url','https://worldofwarcraft.blizzard.com/')}])
    return '\n'.join(lines),buttons
def main():
    print('Azeroth Pulse bot is running; Ctrl+C stops it.')
    offset=None
    while True:
        try:
            params={'timeout':25,'allowed_updates':['message']}
            if offset is not None:params['offset']=offset
            req=urllib.request.Request(API+'getUpdates?'+urllib.parse.urlencode(params),headers={'User-Agent':'AzerothPulseBot/1.0'})
            with urllib.request.urlopen(req,timeout=35) as r:updates=json.loads(r.read()).get('result',[])
            for u in updates:
                offset=u['update_id']+1;msg=u.get('message') or {};chat=(msg.get('chat') or {}).get('id');cmd=(msg.get('text') or '').strip().lower().split('@')[0]
                if not chat:continue
                if cmd in ('/start','/help','/about'):
                    send(chat,'✦ Добро пожаловать в Azeroth Pulse!\n\n/start — справка\n/latest — свежие новости\n/top — самые горячие темы\n/digest — пять главных публикаций\n\nХайп — расчётная оценка по доступным сигналам, не официальная статистика.')
                elif cmd.startswith('/latest'):
                    items=sorted(load_items(),key=lambda x:x.get('published',''),reverse=True)[:5];text,kb=list_message(items,'📰 Последние вести Азерота');send(chat,text,kb)
                elif cmd.startswith('/top') or cmd.startswith('/trends'):
                    items=sorted(load_items(),key=lambda x:int(x.get('heat_score',0)),reverse=True)[:5];text,kb=list_message(items,'⚡ РАДАР ХАЙПА АЗЕРОТА');send(chat,text,kb)
                elif cmd.startswith('/digest'):
                    items=sorted(load_items(),key=lambda x:(int(x.get('heat_score',0)),x.get('published','')),reverse=True)[:5]
                    if items:
                        lines=['✦ AZEROTH PULSE — главное за день','']
                        for i,x in enumerate(items,1):lines.extend([f"{i}. {x.get('title_ru') or x.get('title')}",(x.get('ai_summary') or x.get('summary') or '')[:240],x.get('url',''),''])
                        kb=[[{'text':f'Читать #{i} ↗','url':x.get('url','https://worldofwarcraft.blizzard.com/')} ] for i,x in enumerate(items,1)]
                        send(chat,'\n'.join(lines),kb)
                    else:send(chat,'Свежих публикаций пока нет.')
                else:send(chat,'Команда не найдена. Используй /latest, /top или /digest.')
        except KeyboardInterrupt:break
        except Exception as e:print('Polling error:',e);time.sleep(4)
if __name__=='__main__':main()
