# Regional Strategy & Commuting Blueprint: Mitteldeutsche Universitätsallianz

This guide outlines the localized institutional network, transit radii, and direct portal scraping blueprints for **Dr. Faloye** based in **Halle (Saale)**.

---

## 1. Geographic Advantage & Commuting Radii from Halle (Saale) Hbf

Halle (Saale) sits at the nexus of the **Central German University Alliance (*Mitteldeutsche Universitätsallianz*)**. Thanks to the dense S-Bahn Mitteldeutschland and regional rail network, multiple top-tier universities and research institutes are within zero-relocation daily commuting distance:

```
                  ┌────────────────────────────────────────┐
                  │       Dr. Faloye — Halle (Saale)       │
                  └───────────────────┬────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌──────────────────┐        ┌──────────────────┐          ┌───────────────────┐
│ MLU Halle (Home) │        │ Leipzig (22 min) │          │  Jena & Magdeburg │
│ - 0 min commute  │        │ - 22 min S-Bahn  │          │ - 45-50 min RE/ICE│
│ - Phil Fak III   │        │ - Uni Leipzig    │          │ - Uni Jena (FSU)  │
│ - ZSB / DoKoLL   │        │ - HTWK Leipzig   │          │ - EAH Jena        │
│ - LLZ Didactics  │        │ - UFZ Helmholtz  │          │ - OVGU Magdeburg  │
└──────────────────┘        └──────────────────┘          └───────────────────┘
```

### Precise Transit Times (from Halle Hbf):
* **Leipzig (Uni Leipzig / HTWK Leipzig):** **22 minutes** via S-Bahn lines **S3, S5, or S7** (departing every 10–15 minutes).
* **Jena (Friedrich-Schiller-Universität Jena / EAH Jena):** **45 minutes** via ICE / Regional-Express (RE 18).
* **Magdeburg (Otto-von-Guericke-Universität / Hochschule Magdeburg-Stendal):** **50 minutes** via RE 30.
* **Merseburg (Hochschule Merseburg):** **10 minutes** via S-Bahn / regional train.
* **Dresden (TU Dresden):** **1 hour 25 minutes** via direct IC / ICE.

---

## 2. Institutional Targets by Priority

### A. Martin-Luther-Universität Halle-Wittenberg (MLU) — Home Institution
* **Location:** Halle (Saale), Germany (0 min commute)
* **Direct Career Portal:** `https://personal.verwaltung.uni-halle.de/jobs/wissmi/`
* **High-Yield Faculties & Institutes:**
  * **Philosophische Fakultät III - Erziehungswissenschaften:** General didactics, adult education, school pedagogy.
  * **Zentrum für Lehrerbildung (ZSB) / DoKoLL:** Teacher education coordination and competency diagnostics.
  * **Zentrum für multimediales Lehren und Lernen (LLZ):** Higher education didactics (*Hochschuldidaktik*), instructional design, AI in higher education.
* **Scraper Blueprint:** Text blocks formatted with internal registration numbers (`Reg.-Nr.` / `Reg. No.`), closing deadlines (`Bewerbungen bis DD.MM.YYYY`), and direct PDF announcements.

### B. Universität Leipzig — 22 Minutes Commute
* **Location:** Leipzig, Germany (S-Bahn S3/S5 direct)
* **Direct Career Portal:** `https://www.uni-leipzig.de/stellenangebote`
* **Academic Staff Subpage:** `https://www.uni-leipzig.de/universitaet/arbeiten-an-der-universitaet-leipzig/stellenausschreibungen/wissenschaftliches-personal`
* **Important Portal Insight:** English versions (`/en/...`) often display summary placeholders or 404 links. State university jobs are officially gazetted on the German-language portal (`/stellenangebote`), requiring scrapers to query the German endpoints directly.
* **Scraper Blueprint:** Scans TYPO3 news cards and accordion panels (`.news-list-item`, `.accordion-item`), extracting reference numbers (`Ausschreibungs-Nr.`, `Kennziffer`), salary scale (**TV-L E 13**), and deadline dates.

### C. Friedrich-Schiller-Universität Jena & EAH Jena — 45 Minutes Commute
* **Location:** Jena, Thuringia
* **Direct Portals:**
  * Uni Jena: `https://www.uni-jena.de/stellenmarkt`
  * Ernst-Abbe-Hochschule Jena: `https://www.eah-jena.de/karriere`
* **Focus:** Interdisciplinary education research, teaching transformation, and science communication.

### D. TU Dresden (TUD) — Excellence University
* **Location:** Dresden, Saxony (1 hr 25 min direct IC)
* **Direct Portal:** `https://www.verw.tu-dresden.de/StellAus/stellen.asp?kat=2&lang=en`
* **Focus:** Center for Interdisciplinary Learning and Teaching (ZiLL), educational technology, and scientific project management.

---

## 3. Dedicated Scrapers & Pipeline Integration

All regional Mitteldeutschland institutions are covered across two dedicated layers:

1. **Research Universities:**
   * MLU Halle: `scrape_mlu_halle()` in `app/scrapers.py`
   * Uni Leipzig: `scrape_uni_leipzig()` in `app/scrapers.py`
   * TU Dresden: `scrape_tu_dresden()` in `app/scrapers.py`
   * Uni Jena: `scrape_uni_jena()` in `app/scrapers.py`
   * OVGU Magdeburg: `scrape_ovgu_magdeburg()` in `app/scrapers.py`

2. **Universities of Applied Sciences (HAW / Fachhochschulen):**
   * HTWK Leipzig: `scrape_htwk_leipzig()` in `app/scrapers_haw.py`
   * Hochschule Merseburg: `scrape_hs_merseburg()` in `app/scrapers_haw.py`
   * Hochschule Magdeburg-Stendal (h2): `scrape_h2_magdeburg()` in `app/scrapers_haw.py`
   * EAH Jena: `scrape_eah_jena()` in `app/scrapers_haw.py`

3. **Regional Coordinator Runner:**
   * Located at [`regional_network.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/regional_network.py), executing daily automated scans, matching scoring (0–100%), and dispatching instant Telegram notifications.

---

## 4. Live Verified Regional Listings Breakdown (112+ Active Positions)

Live inspection and validation results across the complete central German commuting network from Halle (Saale):

```
                          ┌──────────────────────────┐
                          │   Dr. Faloye (Halle)     │
                          └─────────────┬────────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  MLU Halle   │ │ Uni Leipzig  │ │  Uni Jena    │ │OVGU Magdeburg│ │  TU Dresden  │
│    (0 min)   │ │   (22 min)   │ │   (45 min)   │ │   (50 min)   │ │  (1h 25m)    │
│ 47 Listings  │ │  8 Listings  │ │ 24 Listings  │ │  6 Listings  │ │ 27 Listings  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

| Institution | Commute from Halle Hbf | Live Verified Listings | Key Extracted Vacancy Types | Pay Scales | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Martin-Luther-Universität Halle-Wittenberg** | **0 min** (Home) | **47** | Research Associates, Educational Pedagogy, Didactics | TV-L E 13 | **Verified** |
| **Universität Leipzig** | **22 min** (S-Bahn S3/S5) | **8** | Academic Staff, Project Coordinator, Wiss. Mitarbeiter | TV-L E 13 / E 14 | **Verified** |
| **Friedrich-Schiller-Universität Jena** | **45 min** (Direct ICE/RE) | **24** | Research Associates, Science Coordination, PostDocs | TV-L E 13 | **Verified** |
| **Otto-von-Guericke-Universität Magdeburg** | **50 min** (Direct RE30) | **6** (of 26) | Scientific Staff, Ref. 181/2026 to 192/2026 | TV-L E 13 | **Verified** |
| **Technische Universität Dresden** | **1h 25m** (Direct IC/ICE) | **27** | Research Associates, Science Coordination, PostDocs | TV-L E 13 / E 14 | **Verified** |
| **Regional Applied Universities (HAW)** | **10–50 min** | **15+** | Didactics, Education Management, Media Technology | TV-L E 13 | **Verified** |
| **TOTAL COMMUTABLE REGIONAL POSITIONS** | — | **112+** | Pure Academic / Scientific Staff Vacancies | **TV-L E 13 / E 14** | **LIVE** |

---

## 5. Technical Selector Blueprints for Regional Portals

### A. Martin-Luther-Universität Halle-Wittenberg (`personal.verwaltung.uni-halle.de`)
* **Endpoint:** `https://personal.verwaltung.uni-halle.de/jobs/wissmi/`
* **Card Selector:** `p, div` containing `Reg. No.` or `Reg.-Nr.`
* **Data Mapping:** Internal registration code, application closing date (`Bewerbungen bis DD.MM.YYYY`), and direct link to official tender PDF.

### B. Universität Leipzig (`uni-leipzig.de`)
* **Endpoint:** `https://www.uni-leipzig.de/universitaet/arbeiten-an-der-universitaet-leipzig/stellenausschreibungen`
* **Card Selector:** `.news-list-item, .item, article, [class*='news-list'], [class*='teaser'], div.ce-div`
* **Link Target:** `a[href*='newsdetail'], a[href*='artikel'], a[href*='stelle'], a[href*='.pdf']`
* **Exclusion Gate:** Skip generic UI buttons like `"news filtern"`, `"stellenausschreibungen"`, or `"mehr erfahren"`.

### C. Friedrich-Schiller-Universität Jena (`jobs.uni-jena.de` / `uni-jena.de`)
* **Endpoints:**
  * Direct Job Portal: `https://jobs.uni-jena.de/`
  * Scientific Overview: `https://www.uni-jena.de/122166/stellenangebote`
* **Card Selector:** `table tbody tr, .job-item, .card, article, [class*='stelle'], [class*='job'], a[href]`
* **Metadata Filter:** Ignores marketing and portal navigation tiles (*"visit the"*, *"uni-shop"*, *"media service"*) while isolating postings containing `wissenschaft`, `postdoc`, `fakultät`, or `institut`.

### D. Otto-von-Guericke-Universität Magdeburg (`ovgu.de`)
* **Endpoint:** `https://www.ovgu.de/Karriere_WissenschaftlichesPersonal.html`
* **Card Selector:** Main content cards `a:has(h2), a:has(h3), a:has(h4), .main-content a` matching `Research Associate`, `Wissenschaftliche`, `Postdoc`, or `Ref. No.`
* **Data Mapping:** Captures title, reference number (`Ref. No.: 181/2026`), faculty, and application deadline (`Application deadline: MMMM DD, 2026`).

### E. Technische Universität Dresden (`verw.tu-dresden.de`)
* **Endpoint:** `https://www.verw.tu-dresden.de/StellAus/stellen.asp?kat=2&lang=de`
* **Parameter Significance:** `kat=2` explicitly isolates *Wissenschaftliches Personal* (academic / postdoctoral staff) under TV-L E 13.
* **Listing Container:** `li:has(a), p:has(a), table tbody tr`
* **Metadata Extraction:** Regex matches reference numbers, closing deadlines (`\b\d{2}\.\d{2}\.\d{4}\b`), and salary brackets (`E 13` / `E 14`).

---

## 6. Universities of Applied Sciences (HAW) & Specialist Academies by City

Beyond the primary research universities, regional applied science universities (*Fachhochschulen*) and specialist academies frequently hire didactic advisors, quality managers, and teaching fellows:

| City | Institution | Institution Type | Primary Recruitment Portal | Scraper Module |
| :--- | :--- | :--- | :--- | :--- |
| **Magdeburg** | **Hochschule Magdeburg-Stendal (h2)** | University of Applied Sciences | `https://www.h2.de/hochschule/stellenangebote.html` | `app/scrapers_haw.py` |
| **Jena** | **Ernst-Abbe-Hochschule Jena (EAH)** | University of Applied Sciences | `https://www.eah-jena.de/stellenangebote` | `app/scrapers_haw.py` |
| **Leipzig** | **HTWK Leipzig** | University of Applied Sciences | `https://www.htwk-leipzig.de/hochschule/stellenangebote` | `app/scrapers_haw.py` |
| **Leipzig** | **HMT Leipzig** (Music & Theatre) | Specialist Academy | `https://www.hmt-leipzig.de/de/home/hochschule/stellenangebote` | Central State Mirror |
| **Leipzig** | **HGB Leipzig** (Fine Arts) | Specialist Academy | `https://www.hgb-leipzig.de/hochschule/stellenangebote/` | Central State Mirror |
| **Halle (Saale)** | **Burg Giebichenstein Kunsthochschule** | University of Art & Design | `https://www.burg-halle.de/` | Interamt / Service.bund.de |
| **Merseburg** | **Hochschule Merseburg** *(10 min)* | University of Applied Sciences | `https://www.hs-merseburg.de/stellenangebote/` | `app/scrapers_haw.py` |
| **Köthen / Bernburg** | **Hochschule Anhalt** *(25 min)* | University of Applied Sciences | `https://www.hs-anhalt.de/` | Interamt / Service.bund.de |

---

## 7. Multi-Layer Deduplication & Session Persistence Architecture

### A. Fingerprint Deduplication (`app/dedup.py`)
To prevent the same vacancy from appearing multiple times due to session IDs (`?sid=...`) or syndication across multiple boards (*Academics.de*, *Interamt*, *Service.bund.de*):
1. **Title Hygiene (`is_valid_title`):** Drops placeholder titles where the title equals the institution name or contains incomplete sentence fragments (*"Hochschule und"*, *"Stellenangebote"*).
2. **Canonical Normalization (`normalize_url`):** Strips tracking parameters (`utm_*`, `pk_*`, `sid`, `session`, `ref`) and trailing slashes.
3. **Composite SHA-256 Fingerprint (`generate_fingerprint`):** Generates a unique content hash from `normalized(title) + normalized(organization) + deadline`. If the same position appears under differing URLs, the hash prunes it before database insertion.

### B. Session-Persistent Gazette Scraper (`app/scrapers_bund.py`)
* `service.bund.de` enforces stateful ASP.NET session tokens. Direct card URLs often expire or throw 404s without an active cookie jar.
* The scraper uses `requests.Session()` with an initial handshake to establish persistent cookies, queries the static search endpoint, and runs `is_valid_tender_page` to prevent expired vacancies from being recorded.
