# Top Property / Housing Websites in Indonesia

> Research snapshot compiled June 2026. Traffic figures are approximate monthly visits
> from SimilarWeb / Semrush rankings (Dec 2025 – Feb 2026) and shift month to month.
> Use these as a relative guide, not exact numbers.

## Ranked by traffic (most visited)

| # | Site | URL | Approx. monthly visits | Type | Notes |
|---|------|-----|------------------------|------|-------|
| 1 | **Rumah123** | https://www.rumah123.com | ~3.2–3.4M | Marketplace portal | Largest and most established. Houses, apartments, land, commercial. Owned by REA Group / 99 Group. Deepest Jabodetabek inventory. |
| 2 | **99.co Indonesia** | https://www.99.co/id | ~680–700K | Marketplace portal | Modern, clean UI with well-structured listing data and good filters. Mobile-leaning traffic. Same parent group as Rumah123. |
| 3 | **Brighton** | https://www.brighton.co.id | (top 3) | Agent network | National real-estate agency (since 2011) with thousands of agents. Houses, apartments, land, villas, shophouses, warehouses. |
| 4 | **Pinhome** | https://www.pinhome.id | (top 5) | Marketplace + services | Listings plus property/household services. #1 most-downloaded property app (2023). Strong new-development (primary) inventory. |
| 5 | **Lamudi** | https://www.lamudi.co.id | ~450–630K | Marketplace portal | Long-established aggregator. Houses, apartments, land, commercial across many regions. Informative descriptions. |

## Other notable platforms

| Site | URL | Type | Notes |
|------|-----|------|-------|
| **Rumah.com** | https://www.rumah.com | Marketplace portal | Long-running major portal (PropertyGuru group). Large national inventory. |
| **OLX Indonesia** | https://www.olx.co.id | General classifieds | Property is one of many categories. More informal, owner-direct listings; data quality varies. |
| **Lazudi** | https://lazudi.com/id-en | Marketplace portal | Buy/rent/sell/manage. Stronger in Bali but covers Indonesia. |
| **Mitula / Properstar / Indonesia-Real.Estate** | various | Aggregators | Re-list from other portals; useful for breadth, weaker as a single canonical source. |

## Quick assessment for scraping Jabodetabek house data

What matters for our use case (price, location, specifications — bedrooms, bathrooms,
land area `LT`, building area `LB`, certificate type, etc.):

- **Rumah123** — Best single source: biggest Jabodetabek volume, consistent listing
  template, structured spec fields. Strongest starting candidate.
- **99.co** — Cleanest structured data and modern markup; often exposes JSON/structured
  data that is easier to parse. Excellent second source or even first if anti-bot is lighter.
- **Lamudi** — Solid structured listings, good regional coverage. Reasonable third source.
- **Brighton / Pinhome** — Good inventory (Pinhome strong on primary/new builds) but more
  bespoke page structures; more per-site work to parse.
- **OLX** — High volume but inconsistent, free-text listings; specs often unstructured.
  Harder to extract clean fields. Lower priority for structured data.

**Suggested starting point:** Rumah123 or 99.co for the cleanest price + location + spec
fields in Jabodetabek, designed so additional sources can be added later.

## Sources

- [Most Visited Real Estate Websites in Indonesia — Semrush](https://www.semrush.com/trending-websites/id/real-estate)
- [Top Real Estate Websites in Indonesia — Semrush](https://www.semrush.com/website/top/indonesia/real-estate/)
- [Top Real Estate Websites Ranking in Indonesia — Similarweb](https://www.similarweb.com/top-websites/indonesia/business-and-consumer-services/real-estate/)
- [7 Top Expat-Friendly Real Estate Platforms in Indonesia — Rumah123](https://www.rumah123.com/en/property-guide/expat-friendly-real-estate-platforms-in-indonesia/)
- [Brighton.co.id](https://www.brighton.co.id/)
- [Pinhome.id](https://www.pinhome.id/)
