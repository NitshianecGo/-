# ✦ Azeroth Pulse — WoW news radar

**Russian setup guide:** see [`README_RU.md`](README_RU.md).

A responsive Russian/English World of Warcraft news site with a five-day feed, trend score, source/status labels, event coverage, favorites, video embeds, PNG share cards, PWA/offline shell and an optional Telegram bot. The website is static; GitHub Pages hosts it for free. GitHub Actions collects and updates the feed. Core Python scripts have no third-party dependencies.

## What's included

- **News feed:** public RSS/Atom from the current Blizzard News World of Warcraft feed, Wowhead, MMO-Champion, Google News searches, YouTube search feeds and Reddit's public JSON endpoint.
- **Five-day window:** old/undated records are excluded by the collector; the browser applies a second five-day check.
- **Deduplication:** URL normalization and fuzzy title matching merge likely duplicate stories and retain source links.
- **Hype radar (0–100):** estimated score from freshness, multi-source coverage, topic signals and public Reddit score/comment count when accessible. It is explicitly not actual view counts or Blizzard analytics.
- **Credibility labels:** Blizzard official material, reporting, and unverified leaks/rumours are separated. A model cannot upgrade a non-Blizzard publication into an official source.
- **Optional AI summaries:** configure `OPENAI_API_KEY` as a GitHub Actions secret to write short Russian summaries, tags and a “why it matters” note into the JSON feed. The key is not shipped to the browser. Without it, the site still works with source excerpts. AI cannot promote non-Blizzard sources into official status.
- **Events radar:** detects event/schedule coverage from recent publications. Dates display only when a literal date can be extracted from the source text; no dates are invented.
- **Filters:** category, Retail/Classic/Hardcore/PvP/lore, credibility, text search and sorting by newest/hype/source.
- **Favorites:** saved locally in the user's current browser/device; no account required.
- **Share tools:** copy links, Telegram share, native mobile share where supported, downloadable PNG share cards.
- **Videos:** YouTube links can open in a modal player; other source video links open the original page.
- **Daily Telegram digest:** optional scheduled message through GitHub Actions.
- **Interactive Telegram bot:** optional polling script with `/latest`, `/top`, `/digest`, `/help`.
- **PWA/offline shell:** install affordance and cached application files. To refresh news data, a connection is needed.
- **Riko scout mascot:** original inline vector mascot for the Little Azeroth Friends-inspired identity.

## Publish to GitHub Pages

1. Extract the ZIP and create a **public** GitHub repository, for example `azeroth-pulse`.
2. Upload the **contents** of the folder into the repository root. Keep `.github/workflows/` in place. If using the GitHub browser uploader, ensure the hidden `.github` folder is uploaded too; using Git is often simpler.
3. Open **Settings → Pages → Build and deployment** and set **Source: GitHub Actions**.
4. Open **Actions → Update WoW news → Run workflow**. It collects recent stories, commits `data/news.json`, builds the static site bundle, and deploys it to Pages.
5. When the workflow finishes successfully, open **Settings → Pages** to find the published URL. Each scheduled update also deploys the newest JSON feed.

The collector is scheduled every four hours (`17 */4 * * *`, UTC). GitHub can delay or pause scheduled workflows; run the workflow manually if the feed is stale. Enable Actions at **Settings → Actions → General** if necessary.

## Optional AI summaries

1. Create an API key in your OpenAI API account.
2. In the repository open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name it `OPENAI_API_KEY` and paste the key as value. Never hardcode a key in `app.js`, `index.html`, or other public files.
4. Default model is `gpt-4.1-mini`. To override it, create an Actions variable `OPENAI_MODEL` with a model accessible to your API account.
5. `AI_MAX_ITEMS` is set to 18 per run in `update-news.yml`; lower it if you want to limit API use. The API may cost money. Remove the secret or set `ENABLE_AI_SUMMARIES=false` to disable AI. RSS excerpts remain available without AI.

AI summaries are editorial aids, not sources of truth. They only see article titles and excerpts and can make mistakes; open the original story for important details.

## Optional daily Telegram digest

1. In Telegram, open `@BotFather`, create a bot and copy its token.
2. Start the bot once with `/start` in Telegram. Add repository Actions secrets: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (your numeric user/chat ID or a channel ID; you can obtain your personal ID with `@userinfobot`). For channels, add the bot and give it permission to post.
3. Optional: create an Actions variable `AZEROTH_SITE_URL` with the published GitHub Pages URL.
4. Run **Actions → Telegram daily digest → Run workflow** to test. Scheduled dispatch is 09:00 UTC each day. If secrets are absent, that workflow safely skips the sending step.

## Optional command bot

The scheduled digest and an interactive command bot are different things. The digest workflow sends a daily message; the command bot requires a continuously running process. Run it on an always-on machine or supported host with Python 3.10+.

**Windows PowerShell**
```powershell
$env:TELEGRAM_BOT_TOKEN="paste-token-here"
$env:AZEROTH_NEWS_URL="https://YOUR-USERNAME.github.io/azeroth-pulse/data/news.json"
python scripts/telegram_bot.py
```

**macOS/Linux**
```bash
export TELEGRAM_BOT_TOKEN="paste-token-here"
export AZEROTH_NEWS_URL="https://YOUR-USERNAME.github.io/azeroth-pulse/data/news.json"
python3 scripts/telegram_bot.py
```

Bot commands: `/start`, `/latest`, `/top`, `/digest`. Keep the process alive for commands to work; GitHub Actions cron is not a permanent bot host. Never commit the bot token to Git.

## Notes / limitations

- RSS endpoints and public APIs can be rate-limited, blocked, delayed or changed. Check Action logs to see sources skipped during a run. If all upstream sources temporarily fail, the collector keeps the previous feed rather than overwriting fresh items with an empty list; a first-run total outage is shown as a source error instead of being mistaken for an empty news day.
- Some feeds omit images, descriptions, or exact event dates. No thumbnail/date is fabricated where the source has none.
- Reddit scores/comments are an available engagement signal, not a global popularity measure. YouTube search RSS does not provide reliable view-count growth, so no fake video stats are shown.
- The trend score is an approximate discovery tool, not verified analytics.
- GitHub Pages is static and cannot safely store API keys or host a permanent bot. AI runs in Actions; the interactive bot needs an always-on process.
- Favorites are local to a browser/device and do not sync.
- The page links to original articles instead of republishing complete stories. Image copyrights remain with their publishers.
- Unofficial fan project; not affiliated with Blizzard Entertainment.

## Local checks

```bash
python -m py_compile scripts/fetch_news.py scripts/telegram_bot.py scripts/telegram_digest.py
python -m unittest discover -s tests
node --check app.js # if Node.js is installed
```
