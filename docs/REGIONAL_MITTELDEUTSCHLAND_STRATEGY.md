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
