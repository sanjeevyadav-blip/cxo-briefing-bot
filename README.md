# CXO Business Briefing Bot -- free / open-source, no-email build

Fully automated daily business briefing: RSS in, a two-host banter script
out, rendered to audio, and published as a web page you visit whenever
you like. **$0/month, one secret, no email/SMTP dependency.**

| Layer | This build uses |
|---|---|
| 1. Ingestion | Public RSS (6 free Indian sources) + Google News RSS as a workaround for the 4 paywalled sources |
| 2. Ranking | Pure Python keyword/recency scoring -- no LLM call at all |
| 3. Script generation | Groq free-tier API, open-weight model (Llama 3.3) -- not Claude |
| 4. Text-to-speech | Piper -- open source (MIT), runs on CPU, no key |
| 5. Archive | Every day's episode + show notes land in `docs/episodes/`, kept forever in git history |
| 6. Delivery | A GitHub Pages site -- `index.html` with an audio player and source links, rebuilt daily |

## What you need to sign up for

Just one thing: a **Groq account** (console.groq.com) for a free API key.
No email, no SMTP, no app passwords -- removed entirely in this build.

## Setup

1. Push this folder to your GitHub repo (already done if you're reading
   this from the repo).
2. Repo Settings -> Secrets and variables -> Actions -> New repository
   secret -> add **`GROQ_API_KEY`** only.
3. Repo Settings -> Actions -> General -> Workflow permissions -> select
   **"Read and write permissions"** (the workflow needs this to commit
   the built page back to `docs/`).
4. Repo Settings -> Pages -> Source: **Deploy from a branch** -> Branch:
   **main**, folder **/docs** -> Save.
5. Actions tab -> "Daily CXO Business Briefing" -> **Run workflow** to
   test manually before trusting the 11:00 IST schedule.
6. Your page will be live at
   `https://<your-username>.github.io/<repo-name>/` a minute or two
   after the first successful run.

## Important -- this hasn't been run end-to-end yet

This code was written against each tool's documented usage (Piper's CLI,
Groq's Python SDK, standard RSS/GitHub Pages) but this chat environment's
network access doesn't extend to PyPI, Hugging Face, or the Groq API, so
it could not be executed here to confirm every flag and URL still matches
the current released versions. Before you trust the daily schedule:

- Run once via **workflow_dispatch** and read the logs end to end.
- If `piper` CLI flags have changed, `pip show piper-tts` and
  `piper --help` inside the Action (temporarily add a debug step) will
  show the current interface.
- If an RSS URL in `config.yaml` 404s, open the publication's site and
  find its current feed URL (usually linked in the footer or at `/rss`).
- If Groq's free tier terms have changed, console.groq.com/docs has the
  current numbers.

## Tuning

- `config.yaml` holds every knob: which feeds, which keywords count as
  "CXO relevant" or "career relevant", shortlist size, target word count,
  which two Piper voices play Host A/B, and the page title.
- Swap `MODEL` in `scripts/generate_script.py` for any other model Groq
  hosts if you want a different writing style.
- To go from "MVP" (6 free sources) to the full 10-source pipeline,
  replace the Google-News-RSS workaround with a real licensed news API
  for WSJ/FT/Nikkei/Bloomberg Businessweek/Il Sole 24 Ore.

## Known limitations of this free build

- The 4 paywalled sources only contribute headline + snippet (via Google
  News RSS), not full article text.
- Piper's voices are clearly synthetic -- clean, but not podcast-host
  quality.
- GitHub's cron scheduler is "best effort" -- expect the odd day where it
  fires several minutes late.
- Groq's free tier is a third-party dependency with its own uptime and
  rate limits -- if it's down or throttled at 11:00 IST, that day's run
  fails; the workflow doesn't currently retry automatically.
- The episode archive lives in git history under `docs/episodes/` --
  it will grow the repo size over time (roughly 10-15 MB/day at the
  bitrate `tts_render.py` uses). Prune old episodes periodically if that
  matters to you.
