# 🗺️ German Higher Education Regional Expansion Matrix & Scraper Integration Tracker

> **Strategic Objective:** Systematically expand direct portal coverage across all German universities, *Pädagogische Hochschulen* (Teacher Education Universities), and Universities of Applied Sciences (*HAW*), organized by geographic region and commuting proximity from **Halle (Saale)**.
> 
> 🛡️ **Core Architecture Rule:** Adding new scraper sources **never modifies existing filtering, profile scoring, or suppression logic**. All new sources pipe raw vacancy streams directly into the proven 4-layer processor and 3-layer historical suppression memory.

---

## 📊 Summary of Current Coverage Status

| Expansion Tier | Region / Zone | Total Target Institutions | Active in Scraper Suite | Queued for Integration |
| :--- | :--- | :---: | :---: | :---: |
| **Tier 1 (Immediate)** | **Mitteldeutschland (ST, SN, TH)** | 18 | **9 Active** | 9 Queued |
| **Tier 2 (High Transit)** | **Berlin-Brandenburg Hub** | 12 | **5 Active** | 7 Queued |
| **Tier 3 (Direct Rail)** | **Lower Saxony & Central-North** | 11 | **0 Active** | 11 Queued |
| **Tier 4 (Didactics)** | **Baden-Württemberg (PHs & Unis)** | 15 | **4 Active** | 11 Queued |
| **Tier 5 (Mega Density)** | **North Rhine-Westphalia (NRW)** | 16 | **2 Active** | 14 Queued |
| **Tier 6 (National)** | **Bavaria, Hesse & Coastal Hubs** | 22 | **3 Active** | 19 Queued |
| **National Aggregators**| **Federated Boards & Public Sector** | 6 | **6 Active** | 0 Queued |
| **TOTALS** | — | **100 Institutions** | **29 Integrated** | **71 Queued** |

---

## 🧭 Tier 1: Mitteldeutschland (Saxony-Anhalt, Saxony, Thuringia)
*Commute from Halle (Saale): 0 to 85 minutes. Zero relocation required.*

| Status | Institution | Type | City (State) | Commute from Halle | Direct Career Portal | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- |
| ✅ **ACTIVE** | **MLU Halle-Wittenberg** | Research Uni | Halle (ST) | **0 min** | `personal.verwaltung.uni-halle.de/jobs/wissmi/` | Phil Fak III (Erziehungswiss.), ZSB, LLZ Didaktik |
| ✅ **ACTIVE** | **Universität Leipzig** | Research Uni | Leipzig (SN) | **22 min** | `uni-leipzig.de/.../stellenausschreibungen` | Erziehungswissenschaftliche Fak., Hochschuldidaktik |
| ✅ **ACTIVE** | **HTWK Leipzig** | Applied Sci (HAW) | Leipzig (SN) | **25 min** | `jobs.htwk-leipzig.de` | Media/Informatics didactics, Quality Management |
| ✅ **ACTIVE** | **FSU Jena** | Research Uni | Jena (TH) | **45 min** | `jobs.uni-jena.de` | Fak. für Sozial- und Verhaltenswiss., Lehrstuhl Didaktik |
| ✅ **ACTIVE** | **EAH Jena** | Applied Sci (HAW) | Jena (TH) | **45 min** | `eah-jena.de/stellenangebote` | Social & Health pedagogy, Teaching innovation |
| ✅ **ACTIVE** | **OVGU Magdeburg** | Research Uni | Magdeburg (ST) | **50 min** | `ovgu.de/Karriere_WissenschaftlichesPersonal.html` | Humanwissenschaften (FHW), Didaktik & Wiss. Management |
| ✅ **ACTIVE** | **Hochschule Magdeburg-Stendal** | Applied Sci (HAW) | Magdeburg (ST) | **50 min** | `h2.de/hochschule/stellenangebote.html` | Angewandte Humanwissenschaften, Studiengangsentwicklung |
| ✅ **ACTIVE** | **Hochschule Merseburg** | Applied Sci (HAW) | Merseburg (ST) | **10 min** | `hs-merseburg.de/stellenangebote/` | Weiterbildung, Soziale Arbeit & Medienpädagogik |
| ✅ **ACTIVE** | **TU Dresden** | Research Uni | Dresden (SN) | **1h 25m** | `verw.tu-dresden.de/StellAus/` | ZiLL (Interdisziplinäres Lehren & Lernen), Erziehungswiss. |
| ⏳ *Queued* | **TU Chemnitz** | Research Uni | Chemnitz (SN) | **1h 15m** | `tu-chemnitz.de/verwaltung/personal/stellen/` | Zentrum für Lehrerbildung, Philosophische Fakultät |
| ⏳ *Queued* | **TU Bergakademie Freiberg** | Research Uni | Freiberg (SN) | **1h 30m** | `tu-freiberg.de/wirtschaft/karriere/stellenangebote` | Hochschuldidaktik, Qualität in der Lehre |
| ⏳ *Queued* | **Bauhaus-Universität Weimar** | Specialist Uni | Weimar (TH) | **50 min** | `uni-weimar.de/de/universitaet/aktuell/stellenausschreibungen/` | Lehrentwicklung, Digitale Bildungsformate |
| ⏳ *Queued* | **Universität Erfurt** | Research Uni | Erfurt (TH) | **50 min** | `uni-erfurt.de/universitaet/arbeiten-an-der-uni/stellenausschreibungen` | Erziehungswissenschaftliche Fakultät, Schulpädagogik |
| ⏳ *Queued* | **Hochschule Anhalt** | Applied Sci (HAW) | Köthen/Bernburg (ST)| **25 min** | `hs-anhalt.de/` | Interamt / Service.bund.de syndication |
| ⏳ *Queued* | **Burg Giebichenstein Halle** | Art & Design Uni | Halle (ST) | **0 min** | `burg-halle.de/` | Interamt / Service.bund.de syndication |
| ⏳ *Queued* | **Hochschule Nordhausen** | Applied Sci (HAW) | Nordhausen (TH) | **1h 15m** | `hs-nordhausen.de/service/stellenangebote/` | Sozialmanagement, Lehrqualität |
| ⏳ *Queued* | **Hochschule Schmalkalden** | Applied Sci (HAW) | Schmalkalden (TH) | **1h 45m** | `hs-schmalkalden.de/hochschule/stellenangebote.html`| Didaktische Beratung & E-Learning |
| ⏳ *Queued* | **Hochschule Harz** | Applied Sci (HAW) | Wernigerode (ST) | **1h 20m** | `hs-harz.de/stellenangebote/` | Verwaltungswissenschaften, Hochschulentwicklung |

---

## 🏛️ Tier 2: Berlin-Brandenburg Hub
*Commute from Halle (Saale): 60 to 75 minutes via direct ICE. Prime national research density.*

| Status | Institution | Type | City (State) | Direct Career Portal | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **Humboldt-Universität zu Berlin (HU)** | Research Uni | Berlin (BE) | `hu-berlin.de/stellenangebote` | Inst. für Erziehungswissenschaften, Qualitätsmanagement |
| ✅ **ACTIVE** | **Freie Universität Berlin (FU)** | Research Uni | Berlin (BE) | `fu-berlin.de/stellenangebote` | Fachbereich Erziehungswissenschaft & Psychologie |
| ✅ **ACTIVE** | **TU Berlin** | Research Uni | Berlin (BE) | `jobs.tu-berlin.de` | Zentraleinrichtung Wissenschaftliche Weiterbildung & Kooperation |
| ✅ **ACTIVE** | **DIPF Leibniz Institute** | Research Inst | Berlin/Frankfurt | `dipf.de/de/karriere` | Bildungsforschung, Bildungspsychologie |
| ✅ **ACTIVE** | **DZHW (Higher Education Center)** | Research Inst | Berlin/Hannover | `dzhw.eu/karriere` | Higher Education Governance, Student Outcomes |
| ⏳ *Queued* | **Universität Potsdam** | Research Uni | Potsdam (BB) | `uni-potsdam.de/de/arbeiten-an-der-up/stellenangebote/` | Humanwissenschaftliche Fakultät, Zentrum für Lehrerbildung |
| ⏳ *Queued* | **WZB Social Science Center** | Research Inst | Berlin (BE) | `wzb.eu/de/service/stellenangebote` | Ausbildung & Arbeitsmarkt, Bildungssysteme |
| ⏳ *Queued* | **Europa-Universität Viadrina** | Research Uni | Frankfurt/Oder (BB)| `europa-uni.de/de/struktur/verwaltung/dezernat_2/stellenangebote/` | Didaktik, Wissenschaftsmanagement |
| ⏳ *Queued* | **BTU Cottbus-Senftenberg** | Technical Uni | Cottbus (BB) | `b-tu.de/universitaet/karriere/stellenausschreibungen` | Lehr- und Lernforschung, Qualitätsentwicklung |
| ⏳ *Queued* | **HTW Berlin** | Applied Sci (HAW) | Berlin (BE) | `htw-berlin.de/karriere/stellenangebote/` | Zentrum für Lehrentwicklung & Hochschuldidaktik |
| ⏳ *Queued* | **HWR Berlin** | Applied Sci (HAW) | Berlin (BE) | `hwr-berlin.de/hwr-berlin/karriere/offene-stellen/` | Berufs- und Weiterbildung, Didaktische Innovation |
| ⏳ *Queued* | **Fachhochschule Potsdam** | Applied Sci (HAW) | Potsdam (BB) | `fh-potsdam.de/informieren/profil/organisation/stellenangebote` | Sozialpädagogik, Lehrinnovation |

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
*The national epicenter for Teacher Training Universities (*Pädagogische Hochschulen*) and Didactics.*

| Status | Institution | Type | City (State) | Direct Career Portal | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **PH Freiburg** | Teacher Ed Uni | Freiburg (BW) | `stellenangebote.ph-freiburg.de` | Erziehungswissenschaft, Psychologie, Didaktik |
| ✅ **ACTIVE** | **PH Ludwigsburg** | Teacher Ed Uni | Ludwigsburg (BW) | `ph-ludwigsburg.de/stellenangebote` | Pädagogik, Empirische Bildungsforschung |
| ✅ **ACTIVE** | **PH Karlsruhe** | Teacher Ed Uni | Karlsruhe (BW) | `ph-karlsruhe.de/stellenangebote` | Pädagogische Psychologie, Didaktische Entwicklung |
| ✅ **ACTIVE** | **Karriere Baden-Württemberg** | State Portal | State-Wide (BW) | `karriere.baden-wuerttemberg.de` | All BW Universities & Ministries (TV-L E 13/E 14) |
| ⏳ *Queued* | **PH Heidelberg** | Teacher Ed Uni | Heidelberg (BW) | `ph-heidelberg.de/stellenangebote.html` | Erziehungswissenschaften, Qualität der Lehre |
| ⏳ *Queued* | **PH Schwäbisch Gmünd** | Teacher Ed Uni | Schwäbisch Gmünd | `ph-gmuend.de/hochschule/stellenangebote` | Schulpädagogik, Kompetenzmessung |
| ⏳ *Queued* | **PH Weingarten** | Teacher Ed Uni | Weingarten (BW) | `ph-weingarten.de/stellenangebote/` | Empirische Schulforschung, Didaktik |
| ⏳ *Queued* | **Universität Heidelberg** | Research Uni | Heidelberg (BW) | `uni-heidelberg.de/stellenmarkt/` | Psychologisches Institut, Hochschuldidaktik |
| ⏳ *Queued* | **Universität Tübingen** | Research Uni | Tübingen (BW) | `uni-tuebingen.de/universitaet/karriere/newsfullview-stellenangebote/` | Hector-Institut für Empirische Bildungsforschung |
| ⏳ *Queued* | **Universität Freiburg** | Research Uni | Freiburg (BW) | `uni-freiburg.de/universitaet/stellenangebote/` | Institut für Erziehungswissenschaft |
| ⏳ *Queued* | **Universität Stuttgart** | Research Uni | Stuttgart (BW) | `uni-stuttgart.de/universitaet/arbeitgeber/stellenangebote/` | Zentrum für Lehre & Qualitätsentwicklung |
| ⏳ *Queued* | **Universität Mannheim** | Research Uni | Mannheim (BW) | `uni-mannheim.de/ueber-uns/arbeiten-an-der-universitaet/stellenangebote/` | Fakultät für Sozialwissenschaften, Bildungsforschung |
| ⏳ *Queued* | **KIT Karlsruhe** | Technical Uni | Karlsruhe (BW) | `jobs.kit.edu` | Dienstleistungseinheit Studium und Lehre |
| ⏳ *Queued* | **Universität Konstanz** | Research Uni | Konstanz (BW) | `uni-konstanz.de/universitaet/aktuelles-und-medien/stellenangebote/` | Fachbereich Psychologie & Bildungsforschung |
| ⏳ *Queued* | **Universität Hohenheim** | Research Uni | Stuttgart (BW) | `uni-hohenheim.de/stellenangebote` | Didaktik, Wissenschaftsmanagement |

---

## 🏢 Tier 5: North Rhine-Westphalia (NRW)
*Largest concentration of universities and students in the European Union.*

| Status | Institution | Type | City (State) | Direct Career Portal | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **Universität zu Köln** | Research Uni | Köln (NW) | `stellenwerk-koeln.de` | Humanwissenschaftliche Fakultät, Zentrum für Lehrerbildung |
| ✅ **ACTIVE** | **DIE (Deutsches Institut für Erwachsenenbildung)** | Research Inst | Bonn (NW) | `die-bonn.de/institut/karriere/` | Erwachsenenbildung, Weiterbildungsforschung |
| ⏳ *Queued* | **Universität Bonn** | Research Uni | Bonn (NW) | `uni-bonn.de/de/universitaet/karriere` | Dezernat Studium und Lehre, Qualitätsmanagement |
| ⏳ *Queued* | **Universität Münster (WWU)** | Research Uni | Münster (NW) | `uni-muenster.de/karriere/stellenangebote.html`| Fachbereich Erziehungswissenschaft und Sozialwissenschaften |
| ⏳ *Queued* | **Universität Bielefeld** | Research Uni | Bielefeld (NW) | `uni-bielefeld.de/stellenangebote/` | Fakultät für Erziehungswissenschaft, Qualitätsentwicklung |
| ⏳ *Queued* | **Ruhr-Universität Bochum (RUB)** | Research Uni | Bochum (NW) | `stellen.ruhr-uni-bochum.de/` | Institut für Erziehungswissenschaft, Lehrinnovation |
| ⏳ *Queued* | **Universität Duisburg-Essen (UDE)**| Research Uni | Duisburg/Essen | `uni-due.de/stellenangebote/` | Zentrum für Hochschulqualitätsentwicklung (ZHQE) |
| ⏳ *Queued* | **TU Dortmund** | Technical Uni | Dortmund (NW) | `karriere.tu-dortmund.de/` | Institut für Schulentwicklungsforschung (IFS), Didaktik |
| ⏳ *Queued* | **RWTH Aachen** | Technical Uni | Aachen (NW) | `rwth-aachen.de/stellenangebote` | Lehr- und Forschungsgebiet Didaktik |
| ⏳ *Queued* | **Universität Paderborn** | Research Uni | Paderborn (NW) | `uni-paderborn.de/universitaet/stellenangebote/`| Institut für Erziehungswissenschaft, PLAZ Lehrerbildung |
| ⏳ *Queued* | **Universität Siegen** | Research Uni | Siegen (NW) | `uni-siegen.de/stellen/` | Fakultät II - Bildung, Architektur, Künste |
| ⏳ *Queued* | **Bergische Universität Wuppertal**| Research Uni | Wuppertal (NW) | `uni-wuppertal.de/de/universitaet/stellenangebote/`| School of Education, Hochschuldidaktik |
| ⏳ *Queued* | **Heinrich-Heine-Universität Düsseldorf**| Research Uni| Düsseldorf (NW) | `hhu.de/stellenangebote` | Service-Center Studium & Lehre |
| ⏳ *Queued* | **FernUniversität in Hagen** | Distance Research | Hagen (NW) | `fernuni-hagen.de/universitaet/arbeiten/stellenangebote/`| Fak. für Kultur- und Sozialwissenschaften (Didaktik) |
| ⏳ *Queued* | **FH Aachen** | Applied Sci (HAW) | Aachen (NW) | `fh-aachen.de/hochschule/stellenangebote/` | Hochschuldidaktisches Zentrum |
| ⏳ *Queued* | **TH Köln** | Applied Sci (HAW) | Köln (NW) | `th-koeln.de/stellenangebote/` | Zentrum für Lehrentwicklung (ZLE) |

---

## 🏰 Tier 6: Bavaria, Hesse & Coastal Research Hubs

| Status | Institution | Type | City (State) | Direct Career Portal | Target Faculties & Focus |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **LMU München** | Research Uni | München (BY) | `lmu.de/stellenangebote` | Fakultät für Psychologie und Pädagogik |
| ✅ **ACTIVE** | **Stiftung Innovation in der Hochschullehre** | Funding/Gov | Hamburg (HH) | `stiftung-hochschullehre.de` | National Teaching Innovation Grants & Governance |
| ⏳ *Queued* | **Goethe-Universität Frankfurt** | Research Uni | Frankfurt (HE) | `uni-frankfurt.de/stellenangebote` | Fachbereich Erziehungswissenschaften, ZfL |
| ⏳ *Queued* | **Philipps-Universität Marburg** | Research Uni | Marburg (HE) | `uni-marburg.de/de/universitaet/administration/verwaltung/dezernat2/stellenangebote` | FB Erziehungswissenschaften |
| ⏳ *Queued* | **Justus-Liebig-Universität Gießen**| Research Uni | Gießen (HE) | `uni-giessen.de/de/ueber-uns/stellenangebote`| Zentrum für fremdsprachliche & didaktische Kompetenzen |
| ⏳ *Queued* | **Universität Kassel** | Research Uni | Kassel (HE) | `uni-kassel.de/uni/universitaet/karriere/stellenangebote`| INCHER (Higher Education Research Center) |
| ⏳ *Queued* | **TU Darmstadt** | Technical Uni | Darmstadt (HE) | `intern.tu-darmstadt.de/stellenangebote/` | Hochschuldidaktische Arbeitsstelle (HDA) |
| ⏳ *Queued* | **FAU Erlangen-Nürnberg** | Research Uni | Erlangen (BY) | `fau.de/jobs/` | Lehrstuhl für Pädagogische Psychologie |
| ⏳ *Queued* | **Universität Würzburg** | Research Uni | Würzburg (BY) | `uni-wuerzburg.de/aktuelles/stellenangebote/`| Institut für Pädagogik, ProfikLehre |
| ⏳ *Queued* | **Universität Regensburg** | Research Uni | Regensburg (BY) | `uni-regensburg.de/universitaet/stellenangebote/`| Zentrum für Hochschul- und Wissenschaftsdidaktik |
| ⏳ *Queued* | **Universität Bamberg** | Research Uni | Bamberg (BY) | `uni-bamberg.de/stellenangebote/` | Lehrstuhl für Empirische Bildungsforschung |
| ⏳ *Queued* | **Universität Augsburg** | Research Uni | Augsburg (BY) | `uni-augsburg.de/de/jobs/` | Philosophisch-Sozialwissenschaftliche Fakultät |
| ⏳ *Queued* | **Universität Passau** | Research Uni | Passau (BY) | `uni-passau.de/stellenangebote/` | Didaktisches Zentrum, Qualität in Studium & Lehre |
| ⏳ *Queued* | **Universität Bayreuth** | Research Uni | Bayreuth (BY) | `uni-bayreuth.de/stellenangebote` | Zentrum für Weiterbildung & Hochschuldidaktik |
| ⏳ *Queued* | **Universität Mainz (JGU)** | Research Uni | Mainz (RP) | `stellenboerse.uni-mainz.de/` | Fachbereich 02 - Sozialwissenschaften, Medien & Sport |
| ⏳ *Queued* | **Universität Trier** | Research Uni | Trier (RP) | `uni-trier.de/universitaet/verwaltung/stellenangebote/` | Fachbereich I - Pädagogik & Psychologie |
| ⏳ *Queued* | **RPTU Kaiserslautern-Landau** | Technical Uni | Landau (RP) | `rptu.de/stellenangebote` | Zentrum für Empirische Pädagogische Forschung (zepf) |
| ⏳ *Queued* | **Universität Hamburg (UHH)** | Research Uni | Hamburg (HH) | `stellenwerk.de/hamburg` | Hamburger Zentrum für Universitäres Lehren und Lernen |
| ⏳ *Queued* | **Universität Bremen** | Research Uni | Bremen (HB) | `uni-bremen.de/universitaet/die-uni-als-arbeitgeberin/offene-stellen/`| Zentrum für Lehrerinnen-/Lehrerbildung & Didaktik |
| ⏳ *Queued* | **Universität Kiel (CAU)** | Research Uni | Kiel (SH) | `uni-kiel.de/de/stellenangebote` | IPN Leibniz-Institut für die Pädagogik der Naturwissenschaften |
| ⏳ *Queued* | **Universität Rostock** | Research Uni | Rostock (MV) | `uni-rostock.de/stellenangebote/` | Institut für Schulpädagogik und Bildungsforschung |
| ⏳ *Queued* | **Universität Greifswald** | Research Uni | Greifswald (MV) | `uni-greifswald.de/universitaet/information/stellenausschreibungen/`| Institut für Erziehungswissenschaft |

---

## 🌐 National Aggregators & Specialized Public Boards (All Active)

| Status | Portal Name | Scope | Direct URL | Scraper Module |
| :---: | :--- | :--- | :--- | :--- |
| ✅ **ACTIVE** | **Wissenschaftsmanagement-Online** | Higher Ed Governance & Management | `wissenschaftsmanagement-online.de` | `app/scrapers_wissman.py` |
| ✅ **ACTIVE** | **Service.bund.de** | Federal & State Public Service Gazette | `service.bund.de` (4 Academic Tracks) | `app/scrapers_bund.py` |
| ✅ **ACTIVE** | **Interamt.de** | Public ATS & State Civil Service | `interamt.de` (Academic/TV-L E13) | `app/scrapers_interamt.py` |
| ✅ **ACTIVE** | **EURAXESS Germany** | EU & DFG Postdoc Fellowships | `euraxess.ec.europa.eu` | `app/scrapers_euraxess.py` |
| ✅ **ACTIVE** | **Academics.de (ZEIT Group)** | Commercial University Job Board | `academics.de` | `app/scrapers.py` |
| ✅ **ACTIVE** | **Education Research Clearinghouse** | DIPF, DZHW, DIE, StIL, PHs | `dipf.de`, `dzhw.eu`, `die-bonn.de` | `app/scrapers_education.py` |

---

## 🔄 Incremental Integration Protocol (Small Steps)

When expanding the scraper suite:
1. **Target Group Selection:** Select 3–5 queued schools in the same region or software platform (e.g. TYPO3 / Rexx HR / B-ite).
2. **Dedicated Modular Script:** Build the scraper as a standalone module (e.g. `app/scrapers_lower_saxony.py` or `app/scrapers_brandenburg.py`).
3. **Zero Impact on Pipeline Logic:** Raw items return `RawVacancy` objects that feed directly into `process_vacancies(raw)`.
4. **Update This Tracker:** Change status from `⏳ Queued` to `✅ ACTIVE` in this matrix and commit to Git.
