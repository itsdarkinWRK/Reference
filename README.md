# 💻 PCMAN | Full-Stack PC Builder & Tech Forum

---

> ⚠️ **IMPORTANT NOTICE:** PYTHONANYWHERE NO LONGER PROVIDES THE OPTION FOR A FREE DATABASE, THEREFORE THE WEBSITE CURRENTLY DOES NOT HAVE A RUNNING DATABASE.

---

<p align="center">
  <strong>A comprehensive, database-driven web application designed for computer enthusiasts and tech support.</strong>
</p>

<p align="center">
  <a href="https://itsdarkin.pythonanywhere.com" target="_blank">
    <img src="https://img.shields.io/badge/Live%20Demo-⚡%20Visit%20Website-blueviolet?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Live Demo">
  </a>
</p>

---

## 🌟 Key Features

### 🛠️ Custom PC Configurator
An interactive, client-side tool allowing users to select compatible hardware components, calculate total requirements, and plan custom computer builds from scratch.

### 💬 Advanced Community Forum
A robust, modular discussion platform engineered with full dynamic capabilities:
* **`home.html`** • Central dashboard featuring global activity overviews and board indexes.
* **`category.html`** • Target boards organized by hardware, software, or help-desk topics.
* **`topic.html`** • Individual thread view displaying full user conversations.
* **`new_topic.html`** • Content creation wizard for users to publish new discussion threads.
* **`search.html`** • Dynamic, text-based query engine to scan titles and posts instantly.
* **`_topics_list.html`** • Reusable partial component optimized for clean topic rendering.
* **`_replies_list.html`** • Modular partial layout designed to stream nested comments seamlessly.

### 🔒 User Management & Core Hubs
* **Authentication:** Secure registration, session-validated login, and cryptographic password handling.
* **Profiles:** Customized dashboards supporting dynamic metadata and custom avatar uploads.
* **Diagnostics:** Built-in interactive troubleshooting wizard and remote technical assistance tools.

---

## 🛠️ Tech Stack & Architecture

| Layer | Technologies Used |
| :--- | :--- |
| **Backend Framework** | Python 3.x / Flask |
| **Database & ORM** | SQLAlchemy / SQLite |
| **Frontend Engine** | HTML5 / Jinja2 Templates / CSS3 / JavaScript (ES6+) |
| **Hosting & Deployment** | PythonAnywhere |

---

## 📂 Modular Project Structure

The codebase is decoupled using a strict MVC-style layout to separate data models, template views, and routing controllers:

```text
/PCMAN
├── app.py                  # Core application entry point & initialization
├── config.py               # Security keys, environment constants & Database URIs
├── database.py             # SQLAlchemy engine binding and session configuration
├── models.py               # Database Schemas (Users, Topics, Replies, Hardware)
├── routes.py               # Main controller handling application logic & URL routing
│
├── static/                 # Static Asset Pipeline
│   ├── css/
│   │   └── styles.css      # Master stylesheet (Responsive layouts & layout architecture)
│   ├── js/
│   │   ├── alert.js        # Global dynamic toast and notification handler
│   │   └── configurator.js # Complex client-side calculation logic for the PC Builder
│   └── images/             # UI elements, brand logos, and hardware assets
│
└── templates/              # Jinja2 Dynamic Views
    ├── base.html           # Master boilerplate template (Navbar, Footer, Layout)
    ├── index.html          # Dynamic landing dashboard
    ├── login.html          # Secure session entry form
    ├── register.html       # User onboard registration form
    ├── configurator.html   # Sandbox workspace for computer building
    ├── diagnostics.html    # Interactive step-by-step diagnostic panel
    └── forum/              # Modular Discussion Board Architecture
        ├── home.html       
        ├── category.html   
        ├── topic.html      
        ├── new_topic.html  
        ├── search.html     
        ├── _topics_list.html
        └── _replies_list.html