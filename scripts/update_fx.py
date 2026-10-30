#!/usr/bin/env python3
"""Daily exchange-rate updater for ATLAS HUB -> data/fx.json (no API key needed).

Source: ExchangeRate-API open access endpoint (https://open.er-api.com, "Rates By Exchange Rate API").
Writes how many Korean won one unit of each currency is worth, formatted like the site shows it.
If the request fails, the previous data/fx.json is kept unchanged (exit code 0 so other steps still run).
"""
import json, os, sys, urllib.request, datetime

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'fx.json')
URL = 'https://open.er-api.com/v6/latest/USD'

def fmt(v):
    if v >= 100: return '{:,.0f}'.format(v)
    if v >= 1: return '{:.1f}'.format(v)
    if v >= 0.01: return '{:.3f}'.format(v)
    return '{:.4f}'.format(v)

def main():
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'atlas-hub-fx-updater'})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        if d.get('result') != 'success': raise ValueError(d.get('error-type') or 'bad response')
        r = d['rates']; krw = r['KRW']
        rates = {c: fmt(krw / v) for c, v in r.items() if v and c != 'KRW'}
        ts = datetime.datetime.fromtimestamp(d.get('time_last_update_unix', 0), datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=9)))
        out = {'updated': ts.strftime('%Y-%m-%d'), 'source': 'Rates By Exchange Rate API (open.er-api.com)', 'unit': 'KRW per 1 unit', 'rates': rates}
    except Exception as e:
        print('fx update failed, keeping previous file:', e); return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    old = None
    try: old = json.load(open(OUT, encoding='utf-8'))
    except Exception: pass
    if old and old.get('rates') == out['rates']: print('fx unchanged'); return 0
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('wrote', OUT, out['updated'], len(rates), 'currencies, USD =', rates.get('USD'))
    return 0

if __name__ == '__main__':
    sys.exit(main())
