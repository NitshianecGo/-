#!/usr/bin/env python3
"""Send five top stories to Telegram from GitHub Actions; quietly skips if secrets are missing."""
import json, os, urllib.request
from pathlib import Path
DATA=Path(__file__).resolve().parents[1]/'data'/'news.json'
TOKEN=os.getenv('TELEGRAM_BOT_TOKEN','').strip();CHAT=os.getenv('TELEGRAM_CHAT_ID','').strip();SITE=os.getenv('AZEROTH_SITE_URL','').strip()
if not TOKEN or not CHAT:print('Telegram digest skipped: add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID Actions secrets.');raise SystemExit(0)
data=json.loads(DATA.read_text(encoding='utf-8'));items=sorted(data.get('items',[]),key=lambda x:(int(x.get('heat_score',0)),x.get('published','')),reverse=True)[:5]
lines=['✦ AZEROTH PULSE — главное за день','']
for i,x in enumerate(items,1):lines.extend([f"{i}. {x.get('title_ru') or x.get('title','Новость WoW')}",(x.get('ai_summary') or x.get('summary') or '')[:240],f"⚡ Хайп {x.get('heat_score',0)}/100",x.get('url',''),''])
if not items:lines.append('Свежих публикаций пока нет — попробуй заглянуть позже.')
if SITE:lines.extend(['Открыть всю ленту: '+SITE])
payload={'chat_id':CHAT,'text':'\n'.join(lines),'disable_web_page_preview':False}
req=urllib.request.Request('https://api.telegram.org/bot'+TOKEN+'/sendMessage',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'AzerothPulseDigest/1.0'})
with urllib.request.urlopen(req,timeout=25) as r:result=json.loads(r.read())
if not result.get('ok'):raise SystemExit('Telegram sendMessage failed: '+str(result.get('description')))
print('Daily digest sent.')
