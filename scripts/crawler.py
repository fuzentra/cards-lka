#!/usr/bin/env python3
"""
LK Card Offers — Sri Lanka Bank Credit Card Promotions Crawler
==============================================================
Scrapes credit card promotion pages from major Sri Lankan banks
and outputs a unified offers.json file.

Banks covered:
  - Commercial Bank (combank.lk)
  - BOC (boc.lk)
  - Seylan (seylan.lk)
  - People's Bank (peoplesbank.lk)
  - HNB (hnb.lk)
  - Sampath Bank (sampath.lk)
  - Nations Trust Bank / AmEx (ntb.lk)
  - Pan Asia Bank (panasiabank.lk)

Usage:
  pip install requests beautifulsoup4 lxml
  python crawler.py

Output:
  offers.json (place this in the same directory as index.html)
"""

import json
import re
import time
import logging
from datetime import date, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
log = logging.getLogger('lk-card-offers')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}
REQUEST_TIMEOUT = 20
DELAY_BETWEEN_REQUESTS = 2  # seconds, be polite

today_str = date.today().isoformat()
year = date.today().year
month_end = f"{year}-{date.today().month:02d}-31"  # approximate; real dates parsed per offer
next_month_end = f"{year}-{(date.today().month % 12) + 1:02d}-30"


# ── Utility ──────────────────────────────────────────────────────────────────

def fetch(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'lxml')
    except Exception as e:
        log.warning(f"Failed to fetch {url}: {e}")
        return None


def parse_date(text: str) -> str:
    """Try to extract a date string from common Sri Lankan bank date formats."""
    if not text:
        return month_end
    text = text.strip()
    # "31st May 2026", "30 June 2026", "31 May 2026"
    patterns = [
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'(\d{4})-(\d{2})-(\d{2})',
    ]
    months = {'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,
              'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            g = m.groups()
            if len(g) == 3 and not g[0].isdigit() or (g[0].isdigit() and len(g[0]) == 4):
                # yyyy-mm-dd
                return f"{g[0]}-{g[1]}-{g[2]}"
            else:
                day, month_name, yr = g[0], g[1].lower(), g[2]
                mo = months.get(month_name, 12)
                return f"{yr}-{mo:02d}-{int(day):02d}"
    return month_end


def categorise(text: str) -> str:
    text = text.lower()
    if any(k in text for k in ['dining','food','restaurant','cafe','coffee','pizza','burger']):
        return 'Dining'
    if any(k in text for k in ['supermarket','grocery','keells','cargills','arpico','retail','shopping','fashion','jewel']):
        return 'Shopping'
    if any(k in text for k in ['hotel','resort','travel','holiday','flight','tour','leisure']):
        return 'Travel'
    if any(k in text for k in ['health','pharmacy','hospital','medical','dental','wellness','spa']):
        return 'Health'
    if any(k in text for k in ['fuel','petrol','solar','education','online']):
        return 'Other'
    return 'Other'


# ── Bank Scrapers ─────────────────────────────────────────────────────────────

def scrape_combank() -> list[dict]:
    """Commercial Bank — combank.lk/rewards-promotions"""
    log.info("Scraping Commercial Bank…")
    soup = fetch('https://www.combank.lk/rewards-promotions')
    if not soup:
        return []

    offers = []
    # ComBank renders offers as cards with class patterns
    cards = soup.select('.offer-card, .promotion-item, .card-item, article, .col-sm-6, .col-md-4')
    for card in cards:
        text = card.get_text(' ', strip=True)
        if 'Off' not in text and 'off' not in text and 'cashback' not in text.lower():
            continue
        # Extract discount percentage
        disc_m = re.search(r'(?:Up to\s+)?(\d+%?\s*(?:Off|off|Cashback|cashback|%\s*off))', text)
        discount = disc_m.group(0).strip() if disc_m else 'Discount'

        # Extract validity
        valid_m = re.search(r'(?:valid|till|until|expires?)[^\d]*(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text, re.IGNORECASE)
        valid_to = parse_date(valid_m.group(1) if valid_m else '')

        title_el = card.select_one('h3, h4, h5, .title, .offer-title, strong')
        title = title_el.get_text(strip=True) if title_el else text[:80]

        if len(title) < 5:
            continue

        offers.append({
            'bank': 'Commercial Bank',
            'bank_id': 'combank',
            'title': title,
            'discount': discount,
            'category': categorise(title + ' ' + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.combank.lk/rewards-promotions',
        })

    # Deduplicate by title
    seen = set()
    unique = []
    for o in offers:
        key = o['title'][:50]
        if key not in seen:
            seen.add(key)
            unique.append(o)

    log.info(f"  ComBank: {len(unique)} offers")
    return unique[:30]


def scrape_boc() -> list[dict]:
    """Bank of Ceylon — boc.lk/personal-banking/card-offers"""
    log.info("Scraping BOC…")
    soup = fetch('https://www.boc.lk/personal-banking/card-offers')
    if not soup:
        return []

    offers = []
    items = soup.select('.offer-item, .promotion, article, .card, .col-md-3, .col-sm-6')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue
        if not any(k in text.lower() for k in ['off', 'cashback', 'discount', 'boc', '%']):
            continue

        disc_m = re.search(r'(\d+%?\s*(?:Off|off|Cashback|cashback))', text)
        discount = disc_m.group(0) if disc_m else 'Special Offer'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h3, h4, h5, strong, .title')
        title = h.get_text(strip=True) if h else text[:80]
        if len(title) < 8:
            title = text[:80]

        offers.append({
            'bank': 'Bank of Ceylon',
            'bank_id': 'boc',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.boc.lk/personal-banking/card-offers',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  BOC: {len(unique)} offers")
    return unique[:25]


def scrape_seylan() -> list[dict]:
    """Seylan Bank — seylan.lk/promotions/cards"""
    log.info("Scraping Seylan…")
    soup = fetch('https://www.seylan.lk/promotions/cards?type[]=credit_card')
    if not soup:
        return []

    offers = []
    items = soup.select('.promo-item, .promotion-card, .card, article, li.promotion')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue

        disc_m = re.search(r'(?:up to\s+)?(\d+%?\s*(?:Off|off|Cashback|cashback|Installment|instalment))', text, re.I)
        discount = disc_m.group(0) if disc_m else 'Special Offer'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h3, h4, h5, .title, strong')
        title = h.get_text(strip=True) if h else text[:80]

        if len(title) < 8:
            continue

        offers.append({
            'bank': 'Seylan Bank',
            'bank_id': 'seylan',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.seylan.lk/promotions/cards',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  Seylan: {len(unique)} offers")
    return unique[:25]


def scrape_peoples() -> list[dict]:
    """People's Bank — peoplesbank.lk/special-offers/"""
    log.info("Scraping People's Bank…")
    soup = fetch('https://www.peoplesbank.lk/special-offers/')
    if not soup:
        return []

    offers = []
    items = soup.select('article, .offer, .promo, .card, .col-md-4, .col-sm-6')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue

        disc_m = re.search(r'(\d+%?\s*(?:Off|off|Cashback|cashback|discount))', text, re.I)
        discount = disc_m.group(0) if disc_m else 'Special Offer'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h2, h3, h4, .title')
        title = h.get_text(strip=True) if h else text[:80]

        if len(title) < 8:
            continue

        offers.append({
            'bank': "People's Bank",
            'bank_id': 'peoples',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.peoplesbank.lk/special-offers/',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  People's Bank: {len(unique)} offers")
    return unique[:25]


def scrape_hnb() -> list[dict]:
    """HNB — hnb.lk/personal/credit-cards/offers"""
    log.info("Scraping HNB…")
    soup = fetch('https://www.hnb.lk/personal/credit-cards/offers')
    if not soup:
        return []

    offers = []
    items = soup.select('article, .offer-item, .promo-card, .card-offer, .col-md-4')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue

        disc_m = re.search(r'(\d+%?\s*(?:Off|off|Cashback|cashback))', text, re.I)
        discount = disc_m.group(0) if disc_m else 'Special Offer'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h3, h4, h5, .title')
        title = h.get_text(strip=True) if h else text[:80]

        if len(title) < 8:
            continue

        offers.append({
            'bank': 'HNB',
            'bank_id': 'hnb',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.hnb.lk/personal/credit-cards/offers',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  HNB: {len(unique)} offers")
    return unique[:25]


def scrape_sampath() -> list[dict]:
    """Sampath Bank — sampath.lk/promotions"""
    log.info("Scraping Sampath Bank…")
    soup = fetch('https://www.sampath.lk/en/promotions')
    if not soup:
        return []

    offers = []
    items = soup.select('article, .promo, .offer, .card, .col-md-4, .col-sm-6')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue

        disc_m = re.search(r'(\d+%?\s*(?:Off|off|Cashback|cashback|instalment))', text, re.I)
        discount = disc_m.group(0) if disc_m else 'Special Offer'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h3, h4, h5, .title, strong')
        title = h.get_text(strip=True) if h else text[:80]

        if len(title) < 8:
            continue

        offers.append({
            'bank': 'Sampath Bank',
            'bank_id': 'sampath',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.sampath.lk/en/promotions',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  Sampath Bank: {len(unique)} offers")
    return unique[:25]


def scrape_ntb() -> list[dict]:
    """Nations Trust Bank / AmEx — ntb.lk"""
    log.info("Scraping NTB…")
    soup = fetch('https://www.ntb.lk/personal/cards/credit-cards/offers')
    if not soup:
        soup = fetch('https://www.americanexpress.lk/offers')
    if not soup:
        return []

    offers = []
    items = soup.select('article, .offer, .promo, .card, .col-md-4')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue

        disc_m = re.search(r'(\d+%?\s*(?:Off|off|Cashback|cashback|Reward))', text, re.I)
        discount = disc_m.group(0) if disc_m else 'Rewards'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h3, h4, h5, .title')
        title = h.get_text(strip=True) if h else text[:80]

        if len(title) < 8:
            continue

        offers.append({
            'bank': 'Nations Trust Bank',
            'bank_id': 'ntb',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.ntb.lk/personal/cards/credit-cards/offers',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  NTB: {len(unique)} offers")
    return unique[:20]


def scrape_pan_asia() -> list[dict]:
    """Pan Asia Bank — panasiabank.lk"""
    log.info("Scraping Pan Asia Bank…")
    soup = fetch('https://www.panasiabank.lk/personal/cards/credit-card-offers')
    if not soup:
        return []

    offers = []
    items = soup.select('article, .offer, .promo, .card, .col-md-4, .col-sm-6')
    for item in items:
        text = item.get_text(' ', strip=True)
        if len(text) < 20:
            continue

        disc_m = re.search(r'(\d+%?\s*(?:Off|off|Cashback|cashback))', text, re.I)
        discount = disc_m.group(0) if disc_m else 'Special Offer'

        date_m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', text)
        valid_to = parse_date(date_m.group(1) if date_m else '')

        h = item.select_one('h3, h4, h5, .title')
        title = h.get_text(strip=True) if h else text[:80]

        if len(title) < 8:
            continue

        offers.append({
            'bank': 'Pan Asia Bank',
            'bank_id': 'pan_asia',
            'title': title,
            'discount': discount,
            'category': categorise(title + text),
            'merchant': '',
            'valid_from': today_str,
            'valid_to': valid_to,
            'url': 'https://www.panasiabank.lk/personal/cards/credit-card-offers',
        })

    seen = set()
    unique = [o for o in offers if not (o['title'][:40] in seen or seen.add(o['title'][:40]))]
    log.info(f"  Pan Asia Bank: {len(unique)} offers")
    return unique[:20]


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    log.info("=" * 50)
    log.info(f"LK Card Offers Crawler — {datetime.now().isoformat()}")
    log.info("=" * 50)

    scrapers = [
        scrape_combank,
        scrape_boc,
        scrape_seylan,
        scrape_peoples,
        scrape_hnb,
        scrape_sampath,
        scrape_ntb,
        scrape_pan_asia,
    ]

    all_offers = []
    for scraper in scrapers:
        try:
            offers = scraper()
            all_offers.extend(offers)
        except Exception as e:
            log.error(f"Scraper {scraper.__name__} failed: {e}")
        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Filter out offers that have already expired
    valid_offers = [o for o in all_offers if o['valid_to'] >= today_str]

    output = {
        'updated': datetime.now().strftime('%d %b %Y, %H:%M'),
        'updated_iso': datetime.now().isoformat(),
        'total': len(valid_offers),
        'offers': valid_offers,
    }

    out_path = Path(__file__).parent / 'offers.json'
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    log.info(f"\n✓ Written {len(valid_offers)} offers to {out_path}")
    log.info(f"  Banks: {len(set(o['bank_id'] for o in valid_offers))} sources")


if __name__ == '__main__':
    run()
