# OurHome 🏠 | Integrated Construction Management Ecosystem

OurHome is a web-based platform designed to organize the construction sector by providing a centralized digital ecosystem for homeowners and professionals. It integrates a verified professional directory with a materials marketplace grounded in government-verified pricing data.

🌐 **Live Platform:** [https://ourhome-production-2ac9.up.railway.app/](https://ourhome-production-2ac9.up.railway.app/)

---

## 🛠️ Core Functionalities

### 1. Verified Professional Directory
[cite_start]A searchable database of contractors, architects, and interior designers[cite: 25, 38]. [cite_start]Users can access verified professional profiles and portfolios to eliminate reliance on informal referral networks[cite: 38, 57].

### 2. Materials Marketplace with Price Transparency
[cite_start]A curated catalog featuring 80+ construction products[cite: 54, 55]. [cite_start]All material pricing is sourced from the **Kerala PWD Schedule of Rates (SOR) 2024** to ensure cost transparency and prevent contractor overcharging[cite: 48, 64, 65].

### 3. AI Bill & Material Analyzer
[cite_start]Integration with the **Groq API (LLaMA 3.3 70B)** allows for automated analysis of contractor quotes[cite: 47, 58]. [cite_start]The system flags potential overpricing and evaluates material suitability based on specific regional climate zones[cite: 59, 60, 61].

---

## ⚙️ Technical Architecture

* [cite_start]**Backend:** Developed using **Django (Python)** with an MVC architecture and ORM for database management[cite: 44].
* [cite_start]**Database:** Powered by **MySQL** for relational data storage of users, products, and verified profiles[cite: 46].
* [cite_start]**Frontend:** Built with **HTML5, CSS3, and JavaScript**, utilizing **HTMX** for dynamic interactions without full page reloads[cite: 42].
* **Media Storage:** Integrated with **Cloudinary CDN** for secure, persistent hosting of project images and profile banners.
* [cite_start]**Authentication:** Secured via **Django Allauth** for role-based access control (Customer vs. Professional)[cite: 45, 63].
* [cite_start]**Deployment:** Hosted on **Railway.app** with automated CI/CD via GitHub integration[cite: 49, 50].

---

## 🛡️ Security & Integrity Measures

* **Credential Isolation:** All API keys (Groq, Cloudinary) and production secrets are managed via environment variables to prevent codebase exposure.
* **History Scrubbing:** Sensitive data and initial database fixtures have been permanently purged from the Git history.
* [cite_start]**Data Validation:** Integration with government-verified SOR data ensures all pricing logic remains objective and transparent[cite: 65, 72].

---

## 👤 Team Details (NG_CP_Team_4865)
* **Sruthi G S** - [LinkedIn](https://www.linkedin.com/in/sruthi-g-s-381b96366) | [cite_start][GitHub](https://github.com/SruthiGS-Gito) [cite: 2, 3]
* [cite_start]**R Anand** [cite: 4]
* [cite_start]**Judith Susan Soney** [cite: 5]
* [cite_start]**Vrinda V** [cite: 6]
* [cite_start]**College:** Sree Buddha College of Engineering, Pattoor [cite: 7]

---
[cite_start]*Developed under the Next Gen Employability Program to bring transparency to the construction industry.* [cite: 8, 72]
