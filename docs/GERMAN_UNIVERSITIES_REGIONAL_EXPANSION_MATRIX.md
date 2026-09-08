# 🗺️ German Higher Education Regional Expansion Matrix & Scraper Integration Tracker

> **Strategic Objective:** Systematically expand direct portal coverage across all German universities, *Pädagogische Hochschulen* (Teacher Education Universities), and Universities of Applied Sciences (*HAW*), organized by geographic region and commuting proximity from **Halle (Saale)**.
> 
> 🛡️ **Core Architecture Rule:** Adding new scraper sources **never modifies existing filtering, profile scoring, or suppression logic**. All new sources pipe raw vacancy streams directly into the proven 4-layer processor and 3-layer historical suppression memory.

---

## 🛠️ Complete Inventory of Existing Scrapers in Codebase (30+ Sources Active)

Below is the verified record of all scraper functions and modules currently active in the repository so we never re-implement existing endpoints:

### 1. Regional Research Universities (Mitteldeutschland)
* **MLU Halle-Wittenberg:** `scrape_mlu_halle()` / `fetch_direct_mlu_halle()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **Universität Leipzig:** `scrape_uni_leipzig()` / `fetch_direct_uni_leipzig()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **TU Dresden:** `scrape_tu_dresden()` / `fetch_direct_tu_dresden()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **FSU Jena:** `scrape_uni_jena()` / `fetch_direct_uni_jena()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **OVGU Magdeburg:** `scrape_ovgu_magdeburg()` / `fetch_direct_ovgu_magdeburg()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)

### 2. Regional Applied Sciences Universities (HAW)
* **HTWK Leipzig:** `scrape_htwk_leipzig()` / `fetch_direct_htwk_leipzig()` in [`app/scrapers_haw.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_haw.py)
* **Hochschule Merseburg:** `scrape_hs_merseburg()` / `fetch_direct_hs_merseburg()` in [`app/scrapers_haw.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_haw.py)
* **Hochschule Magdeburg-Stendal (h2):** `scrape_h2_magdeburg()` / `fetch_direct_h2_magdeburg()` in [`app/scrapers_haw.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_haw.py)
* **Ernst-Abbe-Hochschule Jena (EAH):** `scrape_eah_jena()` / `fetch_direct_eah_jena()` in [`app/scrapers_haw.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_haw.py)
* **HAW Master Aggregator:** `scrape_all_regional_haw()` in [`app/scrapers_haw.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_haw.py)

### 3. Dedicated Teacher Education & Educational Research Institutes
* **PH Freiburg:** `fetch_direct_ph_freiburg()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **PH Ludwigsburg:** `fetch_ph_ludwigsburg_vacancies()` in [`app/scrapers_education.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_education.py)
* **PH Karlsruhe:** `fetch_ph_karlsruhe_vacancies()` in [`app/scrapers_education.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_education.py)
* **DIPF Leibniz Institute for Educational Research:** `fetch_dipf_vacancies()` in [`app/scrapers_education.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_education.py)
* **DZHW Center for Higher Education Research:** `fetch_dzhw_vacancies()` in [`app/scrapers_education.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_education.py)
* **DIE Deutsches Institut für Erwachsenenbildung:** `fetch_die_bonn_vacancies()` in [`app/scrapers_education.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_education.py)
* **Stiftung Innovation in der Hochschullehre (StIL):** `fetch_stil_vacancies()` in [`app/scrapers_education.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_education.py)

### 4. Direct National Research Universities
* **HU Berlin:** `fetch_direct_hu_berlin()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **TU Berlin:** `fetch_direct_tu_berlin()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **LMU München:** `fetch_direct_lmu()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **Universität zu Köln:** `fetch_direct_uni_koeln()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **Universität Heidelberg:** `fetch_direct_uni_heidelberg()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **Universität Münster (WWU):** `fetch_direct_uni_muenster()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)

### 5. National & State Career Portals & Clearinghouses
* **Wissenschaftsmanagement-Online:** `scrape_wissenschaftsmanagement_online()` in [`app/scrapers_wissman.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_wissman.py)
* **Service.bund.de Multi-Track:** `scrape_all_bund_academic_tracks()` in [`app/scrapers_bund.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_bund.py)
* **Interamt.de REST API:** `scrape_interamt()` in [`app/scrapers_interamt.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_interamt.py)
* **EURAXESS Germany:** `scrape_euraxess()` in [`app/scrapers_euraxess.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_euraxess.py)
* **Karriere Baden-Württemberg:** `scrape_karriere_bw()` in [`app/scrapers_karriere_bw.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers_karriere_bw.py)
* **Academics.de:** `fetch_ssr_academics()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **PsychJob:** `fetch_psychjob_direct()` / `fetch_ssr_psychjob()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **H-Soz-Kult:** `fetch_ssr_hsozkult()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)
* **Stellenwerk Network:** `fetch_ssr_stellenwerk()` in [`app/scrapers.py`](file:///c:/Users/hp/Desktop/SkillEdgeup%20postdoc/postdoc-finder/app/scrapers.py)

---

## 📊 Summary of Current Coverage Status

| Expansion Tier | Region / Zone | Total Target Institutions | Active in Scraper Suite | Queued for Integration |
| :--- | :--- | :---: | :---: | :---: |
| **Tier 1 (Immediate)** | **Mitteldeutschland (ST, SN, TH)** | 18 | **9 Active** | 9 Queued |
| **Tier 2 (High Transit)** | **Berlin-Brandenburg Hub** | 12 | **5 Active** | 7 Queued |
| **Tier 3 (Direct Rail)** | **Lower Saxony & Central-North** | 11 | **0 Active** | 11 Queued |
| **Tier 4 (Didactics)** | **Baden-Württemberg (PHs & Unis)** | 15 | **5 Active** | 10 Queued |
| **Tier 5 (Mega Density)** | **North Rhine-Westphalia (NRW)** | 16 | **3 Active** | 13 Queued |
| **Tier 6 (National)** | **Bavaria, Hesse & Coastal Hubs** | 22 | **3 Active** | 19 Queued |
| **National Aggregators**| **Federated Boards & Public Sector** | 6 | **6 Active** | 0 Queued |
| **TOTALS** | — | **100 Institutions** | **31 Active** | **69 Queued** |

---

## 🧭 Tier 1: Mitteldeutschland (Saxony-Anhalt, Saxony, Thuringia)
*Commute from Halle (Saale): 0 to 85 minutes. Zero relocation required.*

| Status | Institution | Type | City (State) | Commute from Halle | Scraper Function & File | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- |
| ✅ **ACTIVE** | **MLU Halle-Wittenberg** | Research Uni | Halle (ST) | **0 min** | `scrape_mlu_halle()` in `scrapers.py` | Phil Fak III (Erziehungswiss.), ZSB, LLZ Didaktik |
| ✅ **ACTIVE** | **Universität Leipzig** | Research Uni | Leipzig (SN) | **22 min** | `scrape_uni_leipzig()` in `scrapers.py` | Erziehungswissenschaftliche Fak., Hochschuldidaktik |
| ✅ **ACTIVE** | **HTWK Leipzig** | Applied Sci (HAW) | Leipzig (SN) | **25 min** | `scrape_htwk_leipzig()` in `scrapers_haw.py` | Media/Informatics didactics, Quality Management |
| ✅ **ACTIVE** | **FSU Jena** | Research Uni | Jena (TH) | **45 min** | `scrape_uni_jena()` in `scrapers.py` | Fak. für Sozial- und Verhaltenswiss., Didaktik |
| ✅ **ACTIVE** | **EAH Jena** | Applied Sci (HAW) | Jena (TH) | **45 min** | `scrape_eah_jena()` in `scrapers_haw.py` | Social & Health pedagogy, Teaching innovation |
| ✅ **ACTIVE** | **OVGU Magdeburg** | Research Uni | Magdeburg (ST) | **50 min** | `scrape_ovgu_magdeburg()` in `scrapers.py`| Humanwissenschaften (FHW), Wiss. Management |
| ✅ **ACTIVE** | **Hochschule Magdeburg-Stendal** | Applied Sci (HAW) | Magdeburg (ST) | **50 min** | `scrape_h2_magdeburg()` in `scrapers_haw.py`| Angewandte Humanwissenschaften, Lehrdidaktik |
| ✅ **ACTIVE** | **Hochschule Merseburg** | Applied Sci (HAW) | Merseburg (ST) | **10 min** | `scrape_hs_merseburg()` in `scrapers_haw.py`| Weiterbildung, Didaktische Beratung |
| ✅ **ACTIVE** | **TU Dresden** | Research Uni | Dresden (SN) | **1h 25m** | `scrape_tu_dresden()` in `scrapers.py` | ZiLL (Interdisziplinäres Lehren & Lernen), Didaktik |
| ⏳ *Queued* | **TU Chemnitz** | Research Uni | Chemnitz (SN) | **1h 15m** | `tu-chemnitz.de/verwaltung/personal/stellen/` | Zentrum für Lehrerbildung, Philosophische Fakultät |
| ⏳ *Queued* | **TU Bergakademie Freiberg** | Research Uni | Freiberg (SN) | **1h 30m** | `tu-freiberg.de/wirtschaft/karriere/stellenangebote` | Hochschuldidaktik, Qualität in der Lehre |
| ⏳ *Queued* | **Bauhaus-Universität Weimar** | Specialist Uni | Weimar (TH) | **50 min** | `uni-weimar.de/de/universitaet/aktuell/stellenausschreibungen/` | Lehrentwicklung, Digitale Bildungsformate |
| ⏳ *Queued* | **Universität Erfurt** | Research Uni | Erfurt (TH) | **50 min** | `uni-erfurt.de/universitaet/arbeiten-an-der-uni/stellenausschreibungen` | Erziehungswissenschaftliche Fakultät, Schulpädagogik |
| ⏳ *Queued* | **Hochschule Anhalt** | Applied Sci (HAW) | Köthen/Bernburg | **25 min** | `hs-anhalt.de/` (Syndicated to Interamt / Bund) | Didaktik & Hochschulentwicklung |
| ⏳ *Queued* | **Burg Giebichenstein Halle** | Art & Design Uni | Halle (ST) | **0 min** | `burg-halle.de/` (Syndicated to Interamt / Bund) | Didaktische Beratung |
| ⏳ *Queued* | **Hochschule Nordhausen** | Applied Sci (HAW) | Nordhausen (TH) | **1h 15m** | `hs-nordhausen.de/service/stellenangebote/` | Sozialmanagement, Lehrqualität |
| ⏳ *Queued* | **Hochschule Schmalkalden** | Applied Sci (HAW) | Schmalkalden (TH) | **1h 45m** | `hs-schmalkalden.de/hochschule/stellenangebote.html`| Didaktische Beratung & E-Learning |
| ⏳ *Queued* | **Hochschule Harz** | Applied Sci (HAW) | Wernigerode (ST) | **1h 20m** | `hs-harz.de/stellenangebote/` | Verwaltungswissenschaften, Hochschulentwicklung |

---

## 🏛️ Tier 2: Berlin-Brandenburg Hub
*Commute from Halle (Saale): 60 to 75 minutes via direct ICE.*

| Status | Institution | Type | City (State) | Scraper Function & File | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **Humboldt-Universität zu Berlin (HU)** | Research Uni | Berlin (BE) | `fetch_direct_hu_berlin()` in `scrapers.py` | Inst. für Erziehungswissenschaften, Qualitätsmanagement |
| ✅ **ACTIVE** | **Freie Universität Berlin (FU)** | Research Uni | Berlin (BE) | Clearinghouse / RSS direct | Fachbereich Erziehungswissenschaft & Psychologie |
| ✅ **ACTIVE** | **TU Berlin** | Research Uni | Berlin (BE) | `fetch_direct_tu_berlin()` in `scrapers.py` | Zentraleinrichtung Wiss. Weiterbildung & Didaktik |
| ✅ **ACTIVE** | **DIPF Leibniz Institute** | Research Inst | Berlin/Frankfurt | `fetch_dipf_vacancies()` in `scrapers_education.py` | Bildungsforschung, Bildungspsychologie |
| ✅ **ACTIVE** | **DZHW (Higher Education Center)** | Research Inst | Berlin/Hannover | `fetch_dzhw_vacancies()` in `scrapers_education.py` | Higher Education Governance, Student Outcomes |
| ⏳ *Queued* | **Universität Potsdam** | Research Uni | Potsdam (BB) | `uni-potsdam.de/de/arbeiten-an-der-up/stellenangebote/` | Humanwissenschaftliche Fakultät, Zentrum für Lehrerbildung |
| ⏳ *Queued* | **WZB Social Science Center** | Research Inst | Berlin (BE) | `wzb.eu/de/service/stellenangebote` | Ausbildung & Arbeitsmarkt, Bildungssysteme |
| ⏳ *Queued* | **Europa-Universität Viadrina** | Research Uni | Frankfurt/Oder | `europa-uni.de/.../stellenangebote/` | Didaktik, Wissenschaftsmanagement |
| ⏳ *Queued* | **BTU Cottbus-Senftenberg** | Technical Uni | Cottbus (BB) | `b-tu.de/universitaet/karriere/stellenausschreibungen` | Lehr- und Lernforschung, Qualitätsentwicklung |
| ⏳ *Queued* | **HTW Berlin** | Applied Sci (HAW) | Berlin (BE) | `htw-berlin.de/karriere/stellenangebote/` | Zentrum für Lehrentwicklung & Hochschuldidaktik |
| ⏳ *Queued* | **HWR Berlin** | Applied Sci (HAW) | Berlin (BE) | `hwr-berlin.de/hwr-berlin/karriere/offene-stellen/` | Berufs- und Weiterbildung, Didaktische Innovation |
| ⏳ *Queued* | **Fachhochschule Potsdam** | Applied Sci (HAW) | Potsdam (BB) | `fh-potsdam.de/.../stellenangebote` | Sozialpädagogik, Lehrinnovation |

---

## 🚆 Tier 3: Lower Saxony & Central-North Hubs
*Commute from Halle/Magdeburg: 60 to 100 minutes via direct IC/ICE.*

| Status | Institution | Type | City (State) | Direct Career Portal | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ⏳ *Queued* | **Georg-August-Universität Göttingen** | Research Uni | Göttingen (NI) | `uni-goettingen.de/de/stellenangebote/` | Pädagogische Psychologie, Didaktik, DFG SFBs |
| ⏳ *Queued* | **Universität Hildesheim** | Research Uni | Hildesheim (NI) | `uni-hildesheim.de/stellenmarkt/` | **High Focus:** Institut für Erziehungswissenschaft, Lehrerbildung |
| ⏳ *Queued* | **Leibniz Universität Hannover** | Research Uni | Hannover (NI) | `uni-hannover.de/de/universitaet/jobs/stellenangebote/` | Zentrum für Qualitätssicherung in Studium und Lehre |
| ⏳ *Queued* | **TU Braunschweig** | Research Uni | Braunschweig (NI)| `tu-braunschweig.de/stellenangebote` | Institut für Erziehungswissenschaft, Lehrinnovation |
| ⏳ *Queued* | **Leuphana Universität Lüneburg** | Research Uni | Lüneburg (NI) | `leuphana.de/universitaet/offene-stellen.html` | Transformative Bildung, Educational Governance |
| ⏳ *Queued* | **Universität Osnabrück** | Research Uni | Osnabrück (NI) | `uni-osnabrueck.de/universitaet/stellenangebote/` | Institut für Erziehungswissenschaft, Psychologie |
| ⏳ *Queued* | **Universität Vechta** | Research Uni | Vechta (NI) | `uni-vechta.de/stellenangebote/` | Bildungs- und Erziehungswissenschaften |
| ⏳ *Queued* | **TU Clausthal** | Technical Uni | Clausthal (NI) | `tu-clausthal.de/universitaet/karriere/stellenangebote` | Hochschuldidaktik, Studienqualität |
| ⏳ *Queued* | **Hochschule Hannover (HsH)** | Applied Sci (HAW) | Hannover (NI) | `hs-hannover.de/ueber-uns/organisation/jobs-karriere/` | Lehr- und Qualitätsmanagement |
| ⏳ *Queued* | **Ostfalia Hochschule** | Applied Sci (HAW) | Wolfenbüttel (NI)| `ostfalia.de/cms/de/pvw/personal/stellenangebote/` | Didaktische Beratung, E-Learning |
| ⏳ *Queued* | **Hochschule Osnabrück** | Applied Sci (HAW) | Osnabrück (NI) | `hs-osnabrueck.de/stellenangebote/` | Kompetenzzentrum Hochschuldidaktik |

---

## 🎓 Tier 4: Baden-Württemberg (Pädagogische Hochschulen & Research Universities)

| Status | Institution | Type | City (State) | Scraper Function & File | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **PH Freiburg** | Teacher Ed Uni | Freiburg (BW) | `fetch_direct_ph_freiburg()` in `scrapers.py` | Erziehungswissenschaft, Psychologie, Didaktik |
| ✅ **ACTIVE** | **PH Ludwigsburg** | Teacher Ed Uni | Ludwigsburg (BW) | `fetch_ph_ludwigsburg_vacancies()` in `scrapers_education.py` | Pädagogik, Empirische Bildungsforschung |
| ✅ **ACTIVE** | **PH Karlsruhe** | Teacher Ed Uni | Karlsruhe (BW) | `fetch_ph_karlsruhe_vacancies()` in `scrapers_education.py` | Pädagogische Psychologie, Didaktische Entwicklung |
| ✅ **ACTIVE** | **Universität Heidelberg** | Research Uni | Heidelberg (BW) | `fetch_direct_uni_heidelberg()` in `scrapers.py` | Psychologisches Institut, Hochschuldidaktik |
| ✅ **ACTIVE** | **Karriere Baden-Württemberg** | State Portal | State-Wide (BW) | `scrape_karriere_bw()` in `scrapers_karriere_bw.py` | All BW Universities & Ministries (TV-L E 13/E 14) |
| ⏳ *Queued* | **PH Heidelberg** | Teacher Ed Uni | Heidelberg (BW) | `ph-heidelberg.de/stellenangebote.html` | Erziehungswissenschaften, Qualität der Lehre |
| ⏳ *Queued* | **PH Schwäbisch Gmünd** | Teacher Ed Uni | Schwäbisch Gmünd | `ph-gmuend.de/hochschule/stellenangebote` | Schulpädagogik, Kompetenzmessung |
| ⏳ *Queued* | **PH Weingarten** | Teacher Ed Uni | Weingarten (BW) | `ph-weingarten.de/stellenangebote/` | Empirische Schulforschung, Didaktik |
| ⏳ *Queued* | **Universität Tübingen** | Research Uni | Tübingen (BW) | `uni-tuebingen.de/.../stellenangebote/` | Hector-Institut für Empirische Bildungsforschung |
| ⏳ *Queued* | **Universität Freiburg** | Research Uni | Freiburg (BW) | `uni-freiburg.de/universitaet/stellenangebote/` | Institut für Erziehungswissenschaft |
| ⏳ *Queued* | **Universität Stuttgart** | Research Uni | Stuttgart (BW) | `uni-stuttgart.de/.../stellenangebote/` | Zentrum für Lehre & Qualitätsentwicklung |
| ⏳ *Queued* | **Universität Mannheim** | Research Uni | Mannheim (BW) | `uni-mannheim.de/.../stellenangebote/` | Fakultät für Sozialwissenschaften, Bildungsforschung |
| ⏳ *Queued* | **KIT Karlsruhe** | Technical Uni | Karlsruhe (BW) | `jobs.kit.edu` | Dienstleistungseinheit Studium und Lehre |
| ⏳ *Queued* | **Universität Konstanz** | Research Uni | Konstanz (BW) | `uni-konstanz.de/.../stellenangebote/` | Fachbereich Psychologie & Bildungsforschung |
| ⏳ *Queued* | **Universität Hohenheim** | Research Uni | Stuttgart (BW) | `uni-hohenheim.de/stellenangebote` | Didaktik, Wissenschaftsmanagement |

---

## 🏢 Tier 5: North Rhine-Westphalia (NRW)

| Status | Institution | Type | City (State) | Scraper Function & File | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **Universität zu Köln** | Research Uni | Köln (NW) | `fetch_direct_uni_koeln()` in `scrapers.py` | Humanwissenschaftliche Fakultät, ZfL |
| ✅ **ACTIVE** | **Universität Münster (WWU)** | Research Uni | Münster (NW) | `fetch_direct_uni_muenster()` in `scrapers.py` | Fachbereich Erziehungswissenschaft und Sozialwiss. |
| ✅ **ACTIVE** | **DIE (Erwachsenenbildung)** | Research Inst | Bonn (NW) | `fetch_die_bonn_vacancies()` in `scrapers_education.py` | Erwachsenenbildung, Weiterbildungsforschung |
| ⏳ *Queued* | **Universität Bonn** | Research Uni | Bonn (NW) | `uni-bonn.de/de/universitaet/karriere` | Dezernat Studium und Lehre, Qualitätsmanagement |
| ⏳ *Queued* | **Universität Bielefeld** | Research Uni | Bielefeld (NW) | `uni-bielefeld.de/stellenangebote/` | Fakultät für Erziehungswissenschaft, Qualitätsentwicklung |
| ⏳ *Queued* | **Ruhr-Universität Bochum (RUB)** | Research Uni | Bochum (NW) | `stellen.ruhr-uni-bochum.de/` | Institut für Erziehungswissenschaft, Lehrinnovation |
| ⏳ *Queued* | **Universität Duisburg-Essen (UDE)**| Research Uni | Duisburg/Essen | `uni-due.de/stellenangebote/` | Zentrum für Hochschulqualitätsentwicklung (ZHQE) |
| ⏳ *Queued* | **TU Dortmund** | Technical Uni | Dortmund (NW) | `karriere.tu-dortmund.de/` | Institut für Schulentwicklungsforschung (IFS), Didaktik |
| ⏳ *Queued* | **RWTH Aachen** | Technical Uni | Aachen (NW) | `rwth-aachen.de/stellenangebote` | Lehr- und Forschungsgebiet Didaktik |
| ⏳ *Queued* | **Universität Paderborn** | Research Uni | Paderborn (NW) | `uni-paderborn.de/universitaet/stellenangebote/`| Institut für Erziehungswissenschaft, PLAZ Lehrerbildung |
| ⏳ *Queued* | **Universität Siegen** | Research Uni | Siegen (NW) | `uni-siegen.de/stellen/` | Fakultät II - Bildung, Architektur, Künste |
| ⏳ *Queued* | **Bergische Universität Wuppertal**| Research Uni | Wuppertal (NW) | `uni-wuppertal.de/de/universitaet/stellenangebote/`| School of Education, Hochschuldidaktik |
| ⏳ *Queued* | **Heinrich-Heine-Universität Düsseldorf**| Research Uni| Düsseldorf (NW) | `hhu.de/stellenangebote` | Service-Center Studium & Lehre |
| ⏳ *Queued* | **FernUniversität in Hagen** | Distance Research | Hagen (NW) | `fernuni-hagen.de/.../stellenangebote/` | Fak. für Kultur- und Sozialwissenschaften (Didaktik) |
| ⏳ *Queued* | **FH Aachen** | Applied Sci (HAW) | Aachen (NW) | `fh-aachen.de/hochschule/stellenangebote/` | Hochschuldidaktisches Zentrum |
| ⏳ *Queued* | **TH Köln** | Applied Sci (HAW) | Köln (NW) | `th-koeln.de/stellenangebote/` | Zentrum für Lehrentwicklung (ZLE) |

---

## 🏰 Tier 6: Bavaria, Hesse & Coastal Research Hubs

| Status | Institution | Type | City (State) | Scraper Function & File | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **LMU München** | Research Uni | München (BY) | `fetch_direct_lmu()` in `scrapers.py` | Fakultät für Psychologie und Pädagogik |
| ✅ **ACTIVE** | **Stiftung Innovation in der Hochschullehre** | Funding/Gov | Hamburg (HH) | `fetch_stil_vacancies()` in `scrapers_education.py` | National Teaching Innovation Grants & Governance |
| ⏳ *Queued* | **Goethe-Universität Frankfurt** | Research Uni | Frankfurt (HE) | `uni-frankfurt.de/stellenangebote` | Fachbereich Erziehungswissenschaften, ZfL |
| ⏳ *Queued* | **Philipps-Universität Marburg** | Research Uni | Marburg (HE) | `uni-marburg.de/.../stellenangebote` | FB Erziehungswissenschaften |
| ⏳ *Queued* | **Justus-Liebig-Universität Gießen**| Research Uni | Gießen (HE) | `uni-giessen.de/.../stellenangebote` | Zentrum für didaktische Kompetenzen |
| ⏳ *Queued* | **Universität Kassel** | Research Uni | Kassel (HE) | `uni-kassel.de/.../stellenangebote` | INCHER (Higher Education Research Center) |
| ⏳ *Queued* | **TU Darmstadt** | Technical Uni | Darmstadt (HE) | `intern.tu-darmstadt.de/stellenangebote/` | Hochschuldidaktische Arbeitsstelle (HDA) |
| ⏳ *Queued* | **FAU Erlangen-Nürnberg** | Research Uni | Erlangen (BY) | `fau.de/jobs/` | Lehrstuhl für Pädagogische Psychologie |
| ⏳ *Queued* | **Universität Würzburg** | Research Uni | Würzburg (BY) | `uni-wuerzburg.de/.../stellenangebote/` | Institut für Pädagogik, ProfikLehre |
| ⏳ *Queued* | **Universität Regensburg** | Research Uni | Regensburg (BY) | `uni-regensburg.de/.../stellenangebote/` | Zentrum für Hochschul- und Wissenschaftsdidaktik |
| ⏳ *Queued* | **Universität Bamberg** | Research Uni | Bamberg (BY) | `uni-bamberg.de/stellenangebote/` | Lehrstuhl für Empirische Bildungsforschung |
| ⏳ *Queued* | **Universität Augsburg** | Research Uni | Augsburg (BY) | `uni-augsburg.de/de/jobs/` | Philosophisch-Sozialwissenschaftliche Fakultät |
| ⏳ *Queued* | **Universität Passau** | Research Uni | Passau (BY) | `uni-passau.de/stellenangebote/` | Didaktisches Zentrum, Qualität in Studium & Lehre |
| ⏳ *Queued* | **Universität Bayreuth** | Research Uni | Bayreuth (BY) | `uni-bayreuth.de/stellenangebote` | Zentrum für Weiterbildung & Hochschuldidaktik |
| ⏳ *Queued* | **Universität Mainz (JGU)** | Research Uni | Mainz (RP) | `stellenboerse.uni-mainz.de/` | FB 02 - Sozialwissenschaften & Medien |
| ⏳ *Queued* | **Universität Trier** | Research Uni | Trier (RP) | `uni-trier.de/.../stellenangebote/` | Fachbereich I - Pädagogik & Psychologie |
| ⏳ *Queued* | **RPTU Kaiserslautern-Landau** | Technical Uni | Landau (RP) | `rptu.de/stellenangebote` | Zentrum für Empirische Pädagogische Forschung (zepf) |
| ⏳ *Queued* | **Universität Hamburg (UHH)** | Research Uni | Hamburg (HH) | `stellenwerk.de/hamburg` | Hamburger Zentrum für Universitäres Lehren und Lernen |
| ⏳ *Queued* | **Universität Bremen** | Research Uni | Bremen (HB) | `uni-bremen.de/.../offene-stellen/` | Zentrum für Lehrerinnen-/Lehrerbildung & Didaktik |
| ⏳ *Queued* | **Universität Kiel (CAU)** | Research Uni | Kiel (SH) | `uni-kiel.de/de/stellenangebote` | IPN Leibniz-Institut für die Pädagogik der Naturwiss. |
| ⏳ *Queued* | **Universität Rostock** | Research Uni | Rostock (MV) | `uni-rostock.de/stellenangebote/` | Institut für Schulpädagogik und Bildungsforschung |
| ⏳ *Queued* | **Universität Greifswald** | Research Uni | Greifswald (MV) | `uni-greifswald.de/.../stellenausschreibungen/` | Institut für Erziehungswissenschaft |
