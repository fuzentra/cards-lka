# cards-lka · Sri Lanka Credit Card Deals

> A [fuzentra](https://fuzentra.com) initiative — aggregating Sri Lankan bank credit card promotions into one daily-updated page.

**Live site:** [fuzentra.github.io/cards-lka](https://fuzentra.github.io/cards-lka)

---

## What it does

A single-page web app that aggregates credit card promotions from all major Sri Lankan banks — dining, shopping, travel, health and more — into one clean, filterable view. Updated daily.

**Key features:**

- **Monthly calendar view** — Mon-first grid with colour-coded offer bars per category; click any date to see that day's deals in a modal
- **Weekday-specific offer logic** — promotions that apply only on certain days (e.g. every Friday) appear only on the correct dates
- **Bank & category filters** — filter by bank (14 supported) or category; active filters stack
- **Today's Deals marquee** — scrolling ticker of offers active today
- **Past-date greying** — dates before today are visually dimmed
- **Dark mode** — full light/dark theme support, follows system preference
- **Mobile-optimised** — responsive layout down to ~380px, no horizontal scroll

---

## Banks covered

Commercial Bank · Bank of Ceylon · Seylan Bank · People's Bank · HNB · Sampath Bank · Nations Trust Bank · Pan Asia Bank · DFCC · NDB · Union Bank · Hatton National Bank · Cargills Bank · NSB

---

## Tech stack

- Pure HTML/CSS/JS — zero build step, zero runtime dependencies
- Google Fonts (Barlow Condensed) — only external resource
- Self-contained single file (`index.html`)
- Offer data embedded as a JS array; updated by a daily scheduled task

---

## Data & updates

Offer data is sourced from official bank websites and embedded directly in `index.html`. A scheduled task runs daily at 03:00 Sri Lanka time (UTC+5:30) to refresh the data.

**Disclaimer:** This page is not affiliated with, endorsed by, or acting on behalf of any bank or financial institution. All promotion details are sourced from publicly available information on official bank websites. Always verify current terms, conditions, and eligibility directly with your bank before redeeming any offer.

---

## Project structure

```
cards-lka/
├── index.html      # Full app — styles, data, and logic in one file
└── README.md
```

---

## Contributing / updating offers

To add or update an offer, edit the `OFFERS` array in `index.html`. Each offer object follows this shape:

```js
{
  "bank": "Bank Name",
  "bank_id": "bank_slug",        // used for CSS colour class
  "title": "Offer title",
  "discount": "20% Off",
  "category": "Dining",          // Dining | Shopping | Travel | Health | Other
  "merchant": "Merchant name",
  "valid_from": "2026-01-01",    // ISO date
  "valid_to": "2026-12-31",      // ISO date
  "days_of_week": [5],           // optional — JS day numbers (0=Sun … 6=Sat)
  "url": "https://bank.lk/offers"
}
```

---

## License

© 2026 fuzentra. Offer details are the intellectual property of their respective banks.
