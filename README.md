# OurHome 🏠 | Integrated Construction Management Ecosystem

OurHome is a web-based platform designed to organize the construction sector by providing a centralized digital ecosystem for homeowners and professionals. It integrates a verified professional directory with a materials marketplace grounded in government-verified pricing data.

🌐 **Live Platform:** [https://ourhome-production-2ac9.up.railway.app/](https://ourhome-production-2ac9.up.railway.app/)

---

## 🛠️ Core Functionalities

### 1. Verified Professional Directory
A searchable database of contractors, architects, and interior designers. Users can access verified professional profiles and portfolios to eliminate reliance on informal referral networks.

### 2. Materials Marketplace with Price Transparency
A curated catalog featuring 80+ construction products. All material pricing is sourced from the **Kerala PWD Schedule of Rates (SOR) 2024** to ensure cost transparency and prevent contractor overcharging.

### 3. AI Bill & Material Analyzer
Integration with the **Groq API (LLaMA 3.3 70B)** allows for automated analysis of contractor quotes. The system flags potential overpricing and evaluates material suitability based on specific regional climate zones.

---

## ⚙️ Technical Architecture

* **Backend:** Developed using **Django (Python)** with an MVC architecture and ORM for database management.
* **Database:** Powered by **MySQL** for relational data storage of users, products, and verified profiles.
* **Frontend:** Built with **HTML5, CSS3, and JavaScript**, utilizing **HTMX** for dynamic interactions without full page reloads.
* **Media Storage:** Integrated with **Cloudinary CDN** for secure, persistent hosting of project images and profile banners.
* **Authentication:** Secured via **Django Allauth** for role-based access control (Customer vs. Professional).
* **Deployment:** Hosted on **Railway.app** with automated CI/CD via GitHub integration.

---

## 🛡️ Security & Integrity Measures

* **Credential Isolation:** All API keys (Groq, Cloudinary) and production secrets are managed via environment variables to prevent codebase exposure.
* **Data Validation:** Integration with government-verified SOR data ensures all pricing logic remains objective and transparent.

---

## 👤 Team Details (NG_CP_Team_4865)
* **Sruthi G S** - [LinkedIn](https://www.linkedin.com/in/sruthi-g-s-381b96366) | [GitHub](https://github.com/SruthiGS-Gito)
* **R Anand**
* **Judith Susan Soney**
* **Vrinda V**
* **College:** Sree Buddha College of Engineering, Pattoor

---
*Developed under the Next Gen Employability Program to bring transparency to the construction industry.*
