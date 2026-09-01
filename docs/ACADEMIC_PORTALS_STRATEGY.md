# Academic Portals, Scoring Context & Technical Extraction Blueprint

This document contains the strategic career context, scoring rubric, and verified portal scraping architectures for the **SkillEdgeUp Post-Doc Finder**.

---

## 1. Strategic Context: The "Postdoc Plus" Track in Germany

In the German higher education landscape, traditional laboratory or chair post-docs represent only one narrow academic route. Universities, Pädagogische Hochschulen (Universities of Education), and non-university research bodies (Leibniz, Helmholtz, Max Planck) have created a vital category of career-grade positions known as **Postdoc Plus**:

* **Wissenschaftsmanagement (Science Management)**
* **Lehrinnovation & Hochschuldidaktik (Higher Education Didactics & Teaching Innovation)**
* **Qualitätsmanagement in Studium und Lehre (Quality Development in Studies & Teaching)**
* **Prorektorat Lehre / Stabsstellen (Governance & Academic Project Coordination)**
* **Bildungsforschung & Kompetenzdiagnostik (Workforce & Educational Research)**

### Key Advantages for Dr. Faloye:

1. **Remuneration (TV-L E 13 / TV-L E 14):**
   * Fully funded, pension-eligible German public sector collective wage agreement (*Tarifvertrag der Länder*).
   * Standard gross starting salary for TV-L E 13 (100%): **~€52,000 – €58,000/year**, scaling to €65,000+ with experience.
2. **Work Permit & Permanent Residency Fast-Track:**
   * **§ 18d AufenthG (Academic Research & Science Permit):** Streamlined visa processing through university hosting agreements (*Aufnahmevereinbarung*).
   * **§ 18g AufenthG (EU Blue Card):** Qualifies easily above statutory minimum salary thresholds, allowing permanent residency (*Niederlassungserlaubnis*) in **21 months** (with B1 German) or **27 months**.
3. **Direct Methodological Alignment with SkillEdgeUp:**
   * Designing competency-based diagnostic frameworks and survey instruments.
   * Directing Training of Trainers (ToT) and faculty development workshops.
   * Quantitative and qualitative program evaluation, accreditation reviews, and strategy briefs for university rectors and deans.

---

## 2. Priority Scoring Rubric (Pipeline Context)

| Target German Role Title | English Equivalent | Pay Scale | Pipeline Score |
| :--- | :--- | :--- | :---: |
| **Referent*in / Koordinator*in für Studium und Lehre** | Coordinator for Academic Affairs & Teaching (Prorektorat) | TV-L E 13 / E 14 | **10 / 10** |
| **Akademische*r Mitarbeiter*in – Lehrinnovation** | Academic Associate – Higher Ed Didactics & Innovation | TV-L E 13 | **10 / 10** |
| **Wissenschaftliche*r Mitarbeiter*in – Bildungsforschung** | Research Associate – Educational Research & Evaluation | TV-L E 13 / E 14 | **9.5 / 10** |
| **Projektkoordinator*in im Prorektorat / Rektorat** | Academic Project Coordinator (Funded Projects) | TV-L E 13 | **9 / 10** |
| **Qualitätsmanager*in Hochschulentwicklung** | Higher Education Quality & Strategy Manager | TV-L E 13 | **8.5 / 10** |
| **Referent*in für Wissenschaftskommunikation & Transfer** | Knowledge Transfer & Science Communication Officer | TV-L E 13 | **8 / 10** |

---

## 3. Platform Architecture & Verified Scraping Blueprints

### A. Wissenschaftsmanagement Online (`wissenschaftsmanagement-online.de`)

* **Portal Purpose:** The central hub in Germany for university administration, academic project leads, and teaching innovation staff.
* **Pagination Structure:** Standard Drupal pagination:
  * Page 1: `https://www.wissenschaftsmanagement-online.de/kategorie/alle-themen/aktivitaeten`
  * Subsequent pages: `?page=1`, `?page=2`, `?page=3`
* **DOM Container:** Every candidate card is wrapped in `<div class="text">`.
* **Metadata Filter Gate:**
  * Real job postings strictly contain at least one of: `Location:`, `Application deadline:`, or `Bewerbungsfrist:`.
  * Editorial articles (`/beitrag/`) and user comments (`/comment/`) do not contain these markers and are filtered out automatically.
* **Author Disambiguation:**
  * The link preceding the title is often `<a href="/users/...">by Author Name</a>`.
  * Anchors containing `/user/` or `/users/` or starting with `by ` are skipped to guarantee that only the true job title anchor is captured.

### B. Academics.de (`academics.de`)

* **Portal Purpose:** The premier German academic job board (ZEIT Verlag) for postdocs, professorships, and science management.
* **Hub URL:** `https://www.academics.de/stellenanzeigen/branche-wissenschaftsmanagement/Sg==`
* **Pagination Structure:** Offset-based pagination:
  * Page 1: Base URL (`?offset=0`)
  * Subsequent pages: `?offset=50`, `?offset=100`
* **DOM Container:** `article`, `div[class*="JobCard"]`, or `div[class*="card"]`.
* **Link Target:** Anchors linking to `a[href*="/jobs/"]`.
* **Institution Extraction:** Employer name appears on separate lines within the card. Auxiliary contract metadata (e.g. `full-time`, `part-time`, `befristet`, `unbefristet`) is stripped to isolate the exact institution name (*Universität Stuttgart*, *PH Freiburg*, *TU München*).

### C. Service.bund.de & Interamt (`service.bund.de`)

* **Portal Purpose:** Official publication platform of the German Federal and State Public Administration where all state university TV-L E 13/E 14 positions are gazetted.
* **Search Endpoint:** `https://www.service.bund.de/Content/DE/Stellen/Suche/Formular.html`
* **Layout Structure:** Tabular grid (`table tbody tr`) or list entries (`.result-list > li`).
* **Column Mapping:**
  * **Column 1 (`td:first-child`):** Contains Job Title (line 1) and Employing Institution (line 2).
  * **Column 3 (`td:nth-child(3)`):** Contains Application Deadline (`DD.MM.YY` / `DD.MM.YYYY`).
* **Soft-Hyphen Normalization:** German words contain invisible Unicode `­` (soft hyphens) between syllables (e.g., `Wis­sen­schafts­ma­na­ger`). Must be sanitized with `.replace('­', '').replace('​', '')` before regex evaluation.
* **Alternative Direct XML Feed:** `https://www.service.bund.de/Content/DE/Stellen/Suche/Formular.html?view=renderRss&templateQueryString={query}` provides session-free XML exports.

---

## 4. Console Validation Snippets (DevTools)

For rapid live inspection directly inside the browser console:

### Academics.de
```javascript
(() => {
  const jobLinks = Array.from(document.querySelectorAll('a[href*="/jobs/"], a[href*="/stellenangebote/"]'));
  const jobs = [];
  jobLinks.forEach((link) => {
    const container = link.closest('article, li, div[class*="card"], div[class*="item"]') || link.parentElement;
    const heading = container.querySelector('h2, h3, h4') || link;
    const title = heading.innerText.trim();
    const lines = container.innerText.split('\n').map(s => s.trim()).filter(Boolean);
    const institution = lines.find(l => l !== title && !l.includes('Full-time') && !l.includes('Part-time') && l.length > 3) || 'Germany (Academic)';
    if (title.length > 8 && !jobs.some(j => j.url === link.href)) {
      jobs.push({ title, institution, url: link.href });
    }
  });
  console.table(jobs);
})();
```

### Wissenschaftsmanagement Online
```javascript
(() => {
  const cards = Array.from(document.querySelectorAll('div.text')).filter(c => {
    const t = c.innerText || '';
    return t.includes('Location:') || t.includes('Application deadline:') || t.includes('Bewerbungsfrist:');
  });
  const jobs = [];
  cards.forEach(card => {
    const links = Array.from(card.querySelectorAll('a[href]'));
    const titleLink = links.find(a => !a.href.includes('/users/') && !a.href.includes('/user/') && a.innerText.trim().length > 5);
    if (titleLink && !jobs.some(j => j.url === titleLink.href)) {
      const cardText = card.innerText.replace(/\s+/g, ' ').trim();
      const deadline = cardText.match(/(?:Application deadline|Bewerbungsfrist|Frist)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})/i)?.[1] || 'Check listing';
      const location = cardText.match(/Location:\s*([^,\n|]+)/i)?.[1]?.trim() || 'Germany';
      jobs.push({ title: titleLink.innerText.trim(), deadline, location, url: titleLink.href });
    }
  });
  console.table(jobs);
})();
```

---

## 5. The 4-Tier Coverage Architecture (Capturing 99% of Openings)

In Germany, higher education is legally devolved to the **16 Federal States (*Länder*)**, not the central federal government. This is why individual university jobs (like Pädagogische Hochschule Freiburg or Uni Heidelberg) often appear on state portals or commercial exchanges before or without reaching federal gazettes (`service.bund.de`).

Instead of building 400 separate university scrapers, the pipeline achieves 99% nationwide coverage using this 4-tier model:

```
┌────────────────────────────────────────────────────────┐
│  Tier 1: Academics.de & Wissenschaftsmanagement-online │
│  (Covers all universities: PH Freiburg, TU9, U15)      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Tier 2: EURAXESS Germany / DAAD                       │
│  (Covers all funded Postdocs & International Grants)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Tier 3: Interamt.de / Service-BW / State Portals      │
│  (State public-service aggregators for all local unis) │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│  Tier 4: Priority Target Universities (Direct SSR)     │
│  (Targeted scrapers for top preferred universities)    │
└────────────────────────────────────────────────────────┘
```

---

## 6. Interamt & State Portals (`interamt.de` / `service-bw.de`)

### Interamt.de
* **Portal Purpose:** The mandated official public service recruitment portal used by German municipal, state, and university administrations.
* **Pay Scales Gazetted:** TV-L E 13 / TV-L E 14, TVöD Bund / VKA, and civil service grades (A 13 / A 14).
* **Direct JSON Endpoint:** `https://www.interamt.de/koop/app/trefferliste` (POST with `suchbegriff`, `page`, `rows`).
* **Mirroring Mechanism:** Official openings from Interamt are mirrored onto `service.bund.de/IMPORTE/Stellenangebote/interamt/`, providing clean access without Wicket session tokens.

### Target University Direct Scraping (e.g. PH Freiburg Rexx HR)
* **Direct SSR URL:** `https://stellenangebote.ph-freiburg.de/stellenangebote.html`
* **Layout Structure:** Standard table rows (`table tbody tr`) with anchors targeting `a[href*="job_angebot"]` or `a[href*="/job/"]`.
* **Exclusion Rules:** Skip generic UI buttons like `"view job"`, `"zu den stellenangeboten"`, or `"stellenbezeichnung"`.
