#!/usr/bin/env python3
"""Daily updater for data/live.json (외교부 해외안전여행 open APIs via data.go.kr).

Python 3 standard library only.

Usage:
    DATA_GO_KR_KEY=... python3 scripts/update_live.py          # live APIs
    python3 scripts/update_live.py --sample                     # offline test → data/live.sample.json
    python3 scripts/update_live.py --out path/to/live.json      # custom output path

Behaviour:
  * Fetches every page of each API (numOfRows/pageNo, totalCount).
  * Normalises to {"updated", "source", "countries": {ISO2: {...}}}.
  * If one API fails, the previous live.json values for that API are kept (merge).
  * Exit code 0 unless ALL API calls fail (then 1, and live.json is left untouched).

Environment overrides (optional):
  DATA_GO_KR_KEY          인증키 (Decoding key preferred; an Encoding key containing '%' is also accepted)
  MOFA_ALARM_URL          default https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2
  MOFA_VISA_URL           default https://apis.data.go.kr/1262000/EntranceVisaService2/getEntranceVisaList2
  MOFA_SPECIAL_URL        default off (2026-10 확인 결과 기존 주소 폐기)
                          (set to "off" to skip the special-advisory API)
"""
import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "scripts", "samples")
DEFAULT_OUT = os.path.join(ROOT, "data", "live.json")
SAMPLE_OUT = os.path.join(ROOT, "data", "live.sample.json")
KST = _dt.timezone(_dt.timedelta(hours=9))
SOURCE = "외교부 해외안전여행 · 공공데이터포털"
MAX_LEN = 60
ROWS = 500          # rows per page
MAX_PAGES = 50      # safety stop

APIS = {
    "alarm": os.environ.get("MOFA_ALARM_URL")
    or "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2",
    "visa": os.environ.get("MOFA_VISA_URL")
    or "https://apis.data.go.kr/1262000/EntranceVisaService2/getEntranceVisaList2",
    # 2026-10-20 확인: SptravelWarningService2 주소는 "서비스 없음(폐기)" 응답 → 기본값은 사용 안 함("off").
    # 새 주소를 찾으면 저장소 Variables 에 MOFA_SPECIAL_URL 로 넣으면 다시 켜져요.
    "special": os.environ.get("MOFA_SPECIAL_URL") or "off",
}

# Fields each API "owns" inside a country record (used for merge-on-failure).
OWNED = {
    "alarm": ("alertLevel", "alert", "alertRegions", "alertDate"),
    "visa": ("visa", "visaRaw"),
    "special": ("special",),
}

ALERT_NAMES = {1: "여행유의", 2: "여행자제", 3: "출국권고", 4: "여행금지"}

# ISO 3166-1 numeric -> alpha-2 (the visa API documents iso_num, not alpha-2).
_ISO_NUM = (
    "004AF 008AL 010AQ 012DZ 016AS 020AD 024AO 028AG 031AZ 032AR 036AU 040AT 044BS 048BH "
    "050BD 051AM 052BB 056BE 060BM 064BT 068BO 070BA 072BW 076BR 084BZ 090SB 092VG 096BN "
    "100BG 104MM 108BI 112BY 116KH 120CM 124CA 132CV 136KY 140CF 144LK 148TD 152CL 156CN "
    "158TW 170CO 174KM 175YT 178CG 180CD 184CK 188CR 191HR 192CU 196CY 203CZ 204BJ 208DK "
    "212DM 214DO 218EC 222SV 226GQ 231ET 232ER 233EE 234FO 238FK 242FJ 246FI 250FR 254GF "
    "258PF 262DJ 266GA 268GE 270GM 275PS 276DE 288GH 292GI 296KI 300GR 304GL 308GD 312GP "
    "316GU 320GT 324GN 328GY 332HT 336VA 340HN 344HK 348HU 352IS 356IN 360ID 364IR 368IQ "
    "372IE 376IL 380IT 384CI 388JM 392JP 398KZ 400JO 404KE 408KP 410KR 414KW 417KG 418LA "
    "422LB 426LS 428LV 430LR 434LY 438LI 440LT 442LU 446MO 450MG 454MW 458MY 462MV 466ML "
    "470MT 474MQ 478MR 480MU 484MX 492MC 496MN 498MD 499ME 500MS 504MA 508MZ 512OM 516NA "
    "520NR 524NP 528NL 531CW 533AW 534SX 540NC 548VU 554NZ 558NI 562NE 566NG 570NU 578NO "
    "580MP 583FM 584MH 585PW 586PK 591PA 598PG 600PY 604PE 608PH 612PN 616PL 620PT 624GW "
    "626TL 630PR 634QA 638RE 642RO 643RU 646RW 652BL 654SH 659KN 660AI 662LC 663MF 666PM "
    "670VC 674SM 678ST 682SA 686SN 688RS 690SC 694SL 702SG 703SK 704VN 705SI 706SO 710ZA "
    "716ZW 724ES 728SS 729SD 732EH 740SR 748SZ 752SE 756CH 760SY 762TJ 764TH 768TG 772TK "
    "776TO 780TT 784AE 788TN 792TR 795TM 796TC 798TV 800UG 804UA 807MK 818EG 826GB 831GG "
    "832JE 833IM 834TZ 840US 850VI 854BF 858UY 860UZ 862VE 876WF 882WS 887YE 894ZM 383XK"
)
ISO_NUM = {tok[:3]: tok[3:] for tok in _ISO_NUM.split()}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- helpers
def first(rec, *keys, default=None):
    """Return first non-empty value among several possible key spellings."""
    if not isinstance(rec, dict):
        return default
    lower = {str(k).lower(): v for k, v in rec.items()}
    for k in keys:
        v = rec.get(k)
        if v is None:
            v = lower.get(k.lower())
        if v is None:
            continue
        if isinstance(v, str):
            v = v.strip()
            if not v or v.lower() in ("null", "none", "-"):
                continue
        return v
    return default


def clean_text(s):
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", s).strip()


def short(s, n=MAX_LEN):
    s = clean_text(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def to_int(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def find_items(payload):
    """Extract the list of records from any known data.go.kr response shape."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    # Shape A: {"response":{"header":..,"body":{"items":{"item":[..]}}}}
    resp = payload.get("response", payload)
    body = resp.get("body", resp) if isinstance(resp, dict) else {}
    for container in (body, resp, payload):
        if not isinstance(container, dict):
            continue
        # Shape B: {"data":[..]}
        for k in ("data", "items", "item", "list"):
            v = container.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
            if isinstance(v, dict):
                inner = v.get("item", v.get("data"))
                if isinstance(inner, list):
                    return [x for x in inner if isinstance(x, dict)]
                if isinstance(inner, dict):
                    return [inner]
            if v == "" or v is None:
                continue
    return []


def meta(payload):
    """(resultCode, resultMsg, totalCount)"""
    if not isinstance(payload, dict):
        return None, None, None
    resp = payload.get("response", payload)
    header = resp.get("header", resp) if isinstance(resp, dict) else {}
    body = resp.get("body", resp) if isinstance(resp, dict) else {}
    code = first(header, "resultCode") if isinstance(header, dict) else None
    if code is None:
        code = first(payload, "resultCode")
    msg = first(header, "resultMsg") if isinstance(header, dict) else None
    if msg is None:
        msg = first(payload, "resultMsg")
    total = None
    for c in (body, resp, payload):
        if isinstance(c, dict) and first(c, "totalCount") is not None:
            total = to_int(first(c, "totalCount"))
            break
    return code, msg, total


class ApiError(Exception):
    pass


def http_get(url, timeout=30, retries=3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "travel-site-live-updater/1.0",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise ApiError(f"network error: {last}")


def parse_body(text):
    t = text.lstrip("﻿").strip()
    if t.startswith("<"):
        # Gateway errors come back as XML even when JSON was requested.
        m = re.search(r"<returnAuthMsg>([^<]+)</returnAuthMsg>", t) or \
            re.search(r"<resultMsg>([^<]+)</resultMsg>", t) or \
            re.search(r"<errMsg>([^<]+)</errMsg>", t)
        raise ApiError("XML/error response: " + (m.group(1) if m else t[:200]))
    try:
        return json.loads(t)
    except ValueError:
        raise ApiError("non-JSON response: " + t[:200])


def build_url(base, key, page):
    # A Decoding key must be URL-encoded; an Encoding key (contains %) is used as-is.
    k = key if "%" in key else urllib.parse.quote(key, safe="")
    q = urllib.parse.urlencode({"returnType": "JSON", "numOfRows": ROWS, "pageNo": page})
    return f"{base}?serviceKey={k}&{q}"


def fetch_all(name, key):
    base = APIS[name]
    items, page, total = [], 1, None
    while page <= MAX_PAGES:
        payload = parse_body(http_get(build_url(base, key, page)))
        code, msg, tot = meta(payload)
        if code is not None and str(code) not in ("0", "00", "000", "INFO-000"):
            raise ApiError(f"resultCode={code} {msg or ''}".strip())
        batch = find_items(payload)
        items.extend(batch)
        if tot is not None:
            total = tot
        if not batch or (total is not None and len(items) >= total) or len(batch) < ROWS:
            break
        page += 1
        time.sleep(0.3)
    return items


def load_sample(name):
    """Sample files: scripts/samples/<name>*.json (each file = one page)."""
    files = sorted(f for f in os.listdir(SAMPLES) if f.startswith(name) and f.endswith(".json"))
    if not files:
        raise ApiError(f"no sample for {name}")
    items = []
    for f in files:
        with open(os.path.join(SAMPLES, f), encoding="utf-8") as fh:
            payload = json.load(fh)
        code, msg, _ = meta(payload)
        if code is not None and str(code) not in ("0", "00", "000", "INFO-000"):
            raise ApiError(f"resultCode={code} {msg or ''}".strip())
        items.extend(find_items(payload))
    return items


# --------------------------------------------------------------------------- ISO resolution
NAME_TO_ISO = {}


def norm_name(s):
    return re.sub(r"[\s·∙().,\-]", "", str(s or "")).lower()


def iso_of(rec):
    v = first(rec, "country_iso_alp2", "countryIsoAlp2", "iso_alp2", "iso_code", "isoCode",
              "country_iso_alpha2", "iso2")
    if isinstance(v, str) and re.fullmatch(r"[A-Za-z]{2}", v.strip()):
        return v.strip().upper()
    num = first(rec, "iso_num", "isoNum", "country_iso_num", "iso_numeric")
    if num is not None:
        n = str(to_int(num) or "").zfill(3)
        if n in ISO_NUM:
            return ISO_NUM[n]
    for k in ("country_nm", "countryName", "country_eng_nm", "countryEnName"):
        nm = norm_name(first(rec, k))
        if nm and nm in NAME_TO_ISO:
            return NAME_TO_ISO[nm]
    return None


def remember_names(rec, iso):
    for k in ("country_nm", "country_eng_nm"):
        nm = norm_name(first(rec, k))
        if nm:
            NAME_TO_ISO.setdefault(nm, iso)


# --------------------------------------------------------------------------- normalisers
def region_label(rec):
    ty = clean_text(first(rec, "region_ty", "regionTy", "region_type", default=""))
    return ty


def norm_alarm(items):
    """Several rows per country are possible (different levels per region)."""
    out = {}
    for rec in items:
        try:
            iso = iso_of(rec)
            if not iso:
                continue
            remember_names(rec, iso)
            lvl = to_int(first(rec, "alarm_lvl", "alarmLvl", "alarm_level", "alert_lvl", "lvl"))
            if lvl is not None and not 0 <= lvl <= 4:
                lvl = None
            region = region_label(rec)
            remark = clean_text(first(rec, "remark", "rmk", "alarm_remark", "region_nm", default=""))
            date = clean_text(first(rec, "written_dt", "wrt_dt", "writtenDt", "reg_dt", default=""))
            c = out.setdefault(iso, {"levels": [], "regions": [], "date": ""})
            if lvl is not None:
                c["levels"].append((lvl, region))
            if lvl:
                desc = f"{lvl}단계"
                if region:
                    desc += f" {region}"
                if remark:
                    desc += f": {remark}"
                c["regions"].append(desc)
            if date > c["date"]:
                c["date"] = date
        except Exception as e:  # never crash on one bad record
            log(f"[alarm] skip bad record: {e!r}")
    result = {}
    for iso, c in out.items():
        if not c["levels"]:
            continue
        lvl = max(l for l, _ in c["levels"])
        partial = any(_is_partial(r) for l, r in c["levels"] if l == lvl) or len(c["levels"]) > 1
        if lvl == 0:
            alert = "여행경보 없음"
        else:
            alert = f"{lvl}단계 {ALERT_NAMES.get(lvl, '')}".strip()
            if partial:
                alert += " (일부 지역)"
        rec = {"alertLevel": lvl, "alert": short(alert)}
        regs = "; ".join(dict.fromkeys(c["regions"]))
        if regs:
            rec["alertRegions"] = short(regs, 300)
        if c["date"]:
            rec["alertDate"] = c["date"][:10]
        result[iso] = rec
    return result


def _is_partial(region):
    r = region or ""
    return bool(r) and not any(w in r for w in ("전체", "전 지역", "전지역", "全"))


def visa_summary(text, yn):
    t = clean_text(text)
    low = t.lower()
    days = None
    # "180일 중 90일" / "90 days within 180" -> the stay length, not the window
    m = re.search(r"\d{1,3}\s*일\s*(?:중|내|이내에|동안)\s*(?:최대\s*)?(\d{1,3})\s*일", t) or \
        re.search(r"(\d{1,3})\s*(?:일|days?)\s*(?:within|in any|in a)", t, flags=re.I) or \
        re.search(r"(\d{1,3})\s*(일|days?)", t, flags=re.I)
    if m:
        days = int(m.group(1))
    else:
        m = re.search(r"(\d{1,2})\s*(개월|months?)", t, flags=re.I)
        if m:
            days = int(m.group(1)) * 30
    eta = re.search(r"\b(e-?ta|esta|etias|eta|k-eta|nzeta|evisitor)\b", low) or \
        any(w in t for w in ("전자여행허가", "전자 여행 허가", "사전 입국 허가", "사전입국허가"))
    on_arrival = any(w in t for w in ("도착비자", "도착 비자", "도착사증", "도착 사증")) or "on arrival" in low
    evisa = any(w in t for w in ("전자비자", "전자 비자", "e-visa", "e-Visa", "eVisa")) or "evisa" in low
    free = any(w in t for w in ("무비자", "무사증", "사증면제", "사증 면제", "비자면제", "비자 면제", "visa free", "visa-free")) \
        or (days is not None and "비자 필요" not in t and "사증 필요" not in t)
    need = any(w in t for w in ("비자 필요", "사증 필요", "비자필요", "사증필요", "사전 비자", "사전 사증"))

    if free and days and not need:
        s = f"무비자 {days}일"
        if eta:
            s += " (전자여행허가 필요)"
        return s
    if eta and not need:
        return "전자여행허가 필요" + (f" · {days}일" if days else "")
    if on_arrival:
        return "도착비자" + (f" {days}일" if days else "")
    if evisa:
        return "전자비자 필요"
    if need:
        return "비자 필요"
    if free:
        return "무비자 입국"
    if t:
        return short(t)
    if isinstance(yn, str) and yn.upper() == "N":
        return "무비자 입국"
    return ""


def norm_visa(items):
    result = {}
    for rec in items:
        try:
            iso = iso_of(rec)
            if not iso:
                continue
            raw = first(rec, "gnrl_pspt_visa_cn", "gnrlPsptVisaCn", "visa_cn", "general_passport_visa_cn",
                        "nvisa_entry_evdc_cn", "remark", default="")
            basis = clean_text(first(rec, "nvisa_entry_evdc_cn", "nvisaEntryEvdcCn", default=""))
            yn = first(rec, "gnrl_pspt_visa_yn", "gnrlPsptVisaYn", "visa_yn")
            summary = visa_summary(raw, yn)
            raw_full = clean_text(raw)
            if basis and basis not in raw_full:
                raw_full = (raw_full + " / 근거: " + basis).strip(" /")
            r = {}
            if summary:
                r["visa"] = short(summary)
            if raw_full:
                r["visaRaw"] = short(raw_full, 400)
            if r:
                result[iso] = r
        except Exception as e:
            log(f"[visa] skip bad record: {e!r}")
    return result


def norm_special(items):
    out = {}
    for rec in items:
        try:
            iso = iso_of(rec)
            if not iso:
                continue
            remember_names(rec, iso)
            region = region_label(rec)
            note = clean_text(first(rec, "evacuate_rcmnd_remark", "evacuation_remark", "remark",
                                    "splimit_note", "sprecommd_note", "special_remark", "note", default=""))
            date = clean_text(first(rec, "written_dt", "wrt_dt", "writtenDt", default=""))[:10]
            parts = ["특별여행주의보"]
            if region:
                parts.append(f"({region})")
            if note:
                parts.append(note)
            if date:
                parts.append(f"· {date}")
            out.setdefault(iso, []).append(" ".join(parts))
        except Exception as e:
            log(f"[special] skip bad record: {e!r}")
    return {iso: {"special": short("; ".join(dict.fromkeys(v)))} for iso, v in out.items()}


NORMALISERS = {"alarm": norm_alarm, "visa": norm_visa, "special": norm_special}


# --------------------------------------------------------------------------- main
def load_previous(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict) and isinstance(d.get("countries"), dict):
            return d
    except (OSError, ValueError):
        pass
    return {"countries": {}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", action="store_true", help="use scripts/samples/*.json instead of the APIs")
    ap.add_argument("--out", default=None,
                    help="output path (default data/live.json; with --sample data/live.sample.json)")
    args = ap.parse_args(argv)
    if args.out is None:
        # Sample values are fake: never let a test run overwrite the real file by accident.
        args.out = SAMPLE_OUT if args.sample else DEFAULT_OUT

    key = (os.environ.get("DATA_GO_KR_KEY") or "").strip()
    if not args.sample and not key:
        log("ERROR: DATA_GO_KR_KEY is not set (GitHub → Settings → Secrets → Actions).")
        return 1

    order = ["alarm", "visa", "special"]  # alarm first: builds the name→ISO map used by others
    if not args.sample and (APIS["special"] or "").lower() == "off":
        order.remove("special")

    prev = load_previous(args.out)
    countries = {k: dict(v) for k, v in prev.get("countries", {}).items() if isinstance(v, dict)}
    status = dict(prev.get("status", {})) if isinstance(prev.get("status"), dict) else {}
    now = _dt.datetime.now(KST).replace(microsecond=0).isoformat()
    ok_count = 0

    for name in order:
        try:
            items = load_sample(name) if args.sample else fetch_all(name, key)
            data = NORMALISERS[name](items)
            if not data:
                raise ApiError(f"0 usable records (raw={len(items)})")
        except Exception as e:
            log(f"[{name}] FAILED, keeping previous values: {e}")
            st = dict(status.get(name, {}))
            st.update({"ok": False, "error": str(e)[:200], "checked": now})
            status[name] = st
            continue
        ok_count += 1
        # Replace this API's fields everywhere (so lifted alerts disappear), then fill in.
        for c in countries.values():
            for f in OWNED[name]:
                c.pop(f, None)
        for iso, fields in data.items():
            countries.setdefault(iso, {}).update(fields)
        status[name] = {"ok": True, "count": len(data), "records": len(items), "updated": now}
        log(f"[{name}] ok: {len(items)} records → {len(data)} countries")

    if ok_count == 0:
        log("ERROR: all API calls failed; live.json left unchanged.")
        return 1

    countries = {k: v for k, v in sorted(countries.items()) if v}
    prev_ok = all(isinstance(s, dict) and s.get("ok") for s in prev.get("status", {}).values() or [None])
    if countries == prev.get("countries") and ok_count == len(order) and prev_ok:
        log("no data changes; live.json left as is (no commit needed).")
        return 0
    out = {"updated": now, "source": SOURCE, "status": status, "countries": countries}
    if args.sample:
        out["sample"] = True  # 테스트용 가짜 데이터 — 사이트에 쓰지 마세요
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, args.out)
    log(f"wrote {args.out}: {len(countries)} countries ({ok_count}/{len(order)} APIs ok)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
