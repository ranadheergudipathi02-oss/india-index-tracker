"""Phase 4 - Telegram alerting. Stdlib only (urllib), so no extra dependency.

Credentials come from env vars TELEGRAM_TOKEN / TELEGRAM_CHAT_ID, or fetcher/secrets.json
(git-ignored). If neither is set, send() is a no-op that just logs - so the pipeline runs
fine before alerting is configured.

Design note - what we alert on:
The master prompt said "alert on zero-changes-across-ALL-indices (silent-block signal)".
But zero *membership* changes is the NORMAL state almost every day (NSE/BSE indices
reconstitute ~2x/year), so alerting on it would fire ~363 days/year = pure noise. A silent
block does not look like "zero changes" - it looks like fetch FAILURES (HTML instead of
JSON/CSV) or empty responses caught by the snapshot guard. So we alert on the health of the
RUN, not on the change count:
  - ok == 0            -> total block / site change          (critical)
  - many failed/guard  -> partial block or upstream breakage  (warning)
  - any failures       -> name the offending indices          (warning)
A healthy run with zero changes is silent by design. (Optional heartbeat: send_heartbeat().)
"""
import os, json, urllib.parse, urllib.request
import config as C

SECRETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.json")


def _creds():
    tok = os.environ.get("TELEGRAM_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not (tok and chat) and os.path.exists(SECRETS):
        try:
            s = json.load(open(SECRETS, encoding="utf-8"))
            tok = tok or s.get("telegram_token")
            chat = chat or s.get("telegram_chat_id")
        except Exception as e:
            print("notify: could not read secrets.json -", e)
    return tok, chat


def send(text):
    tok, chat = _creds()
    if not (tok and chat):
        print("notify: telegram not configured (skipping) ->", text.splitlines()[0])
        return False
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": text,
                                   "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    try:
        with urllib.request.urlopen(url, data=data, timeout=20) as r:
            ok = (r.status == 200)
        print("notify: sent" if ok else "notify: telegram returned non-200")
        return ok
    except Exception as e:
        print("notify: send failed -", e)
        return False


def check_and_alert(meta=None):
    """Inspect a run's meta summary and alert only when the run looks unhealthy."""
    if meta is None:
        meta = json.load(open(C.META_FILE, encoding="utf-8"))
    s = meta.get("summary", {})
    total = s.get("total", 0)
    ok = s.get("ok", 0)
    failed = s.get("failed", 0)
    guard = s.get("guard_skipped", 0)
    changed = s.get("indices_changed", 0)

    alerts = []
    if total and ok == 0:
        alerts.append(f"⛔ ALL {total} indices failed - likely an IP block or an upstream "
                      f"site/endpoint change. Data NOT updated.")
    elif (failed + guard) >= max(5, int(total * 0.2)):
        alerts.append(f"⚠️ Unhealthy run: {failed} failed + {guard} guard-skipped of {total}.")
    elif failed:
        names = [k for k, v in meta.get("indices", {}).items() if v.get("status") == "failed"]
        shown = ", ".join(names[:15]) + (f" (+{len(names)-15} more)" if len(names) > 15 else "")
        alerts.append(f"⚠️ {failed} index fetch failure(s): {shown}")

    if not alerts:
        print(f"notify: healthy run (ok={ok}/{total}, changed={changed}) - no alert")
        return False

    body = (f"<b>Index Tracker - {meta.get('last_run', '')}</b>\n" + "\n".join(alerts) +
            f"\nok={ok}/{total}  failed={failed}  guard={guard}  changed={changed}")
    return send(body)


def send_heartbeat(meta=None):
    """Optional 'still alive' ping (e.g. wire to a weekly trigger). Off by default."""
    if meta is None:
        meta = json.load(open(C.META_FILE, encoding="utf-8"))
    s = meta.get("summary", {})
    return send(f"✅ Index Tracker ok - {meta.get('last_run','')}  "
                f"ok={s.get('ok',0)}/{s.get('total',0)}  changed={s.get('indices_changed',0)}")


if __name__ == "__main__":
    # manual test: `python fetcher/notify.py`  -> evaluates the latest run
    check_and_alert()
