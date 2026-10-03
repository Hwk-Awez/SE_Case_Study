# Software Component Cataloguing System

A centralized web-based repository for software engineering teams and academic institutions to store, classify, search, browse, download, and track the reuse of software assets (code modules and architectural designs).

---

## 1. Project Overview & Motivation

In traditional software development, developers frequently write redundant implementations for standard tasks (authentication, database pooling, form validations, sorting routines, architectural blueprints). The **Software Component Cataloguing System** addresses this problem by providing:

1. **Centralized Repository:** A single internal catalog of approved, verified reusable components.
2. **Dual Asset Types:** Supports both **Code Components** (source files, scripts, utilities) and **Design Components** (UML diagrams, ER schemas, architectural specifications).
3. **Formal Reuse Tracking:** Allows developers to log when and where a component is integrated into a project, producing real metrics on software reuse.
4. **Demand-Driven Query Analytics:** Automatically records search queries and flags zero-result searches to alert repository curators to missing components.
5. **Semantic Search Readiness:** Designed with a modular service layer prepared for Pinecone vector embeddings while providing an intelligent local fallback search engine.

---

## 2. Technology Stack

* **Backend Framework:** Django (Python 3.14+)
* **Database:** SQLite (default local) / PostgreSQL via Supabase (production ready)
* **Frontend:** Django Templates, Vanilla HTML5, Vanilla CSS3, Vanilla JavaScript (Zero bloated frameworks, no React/Tailwind/Bootstrap)
* **Package & Environment Manager:** `uv`
* **Vector Search Preparation:** Pinecone & text embeddings service layer (`services/semantic_search.py`)

---

## 3. Architecture & Project Structure

The project strictly adheres to Django's Model-View-Template (MVT) pattern combined with a dedicated **Services Layer** for search and classification.

```text
SE_Case_Study/
├── manage.py                        # Django command-line execution utility
├── pyproject.toml                   # Project dependencies and packaging
├── uv.lock                          # Dependency lockfile
├── .env.example                     # Environment variables template
├── db.sqlite3                       # Local SQLite database
│
├── catalogue/                       # Project configuration package
│   ├── __init__.py
│   ├── asgi.py                      # ASGI entrypoint
│   ├── settings.py                  # Core configuration (Supabase & Pinecone ready)
│   ├── urls.py                      # Root URL routing & media handlers
│   └── wsgi.py                      # WSGI entrypoint
│
├── components/                      # Core repository application
│   ├── admin.py                     # Django Admin registration
│   ├── apps.py                      # Application config
│   ├── context_processors.py        # Global template context (search status)
│   ├── forms.py                     # ComponentForm & ReuseRecordForm
│   ├── models.py                    # Database models (Category, Component, ReuseRecord, etc.)
│   ├── tests.py                     # Comprehensive test suite (10 test cases)
│   ├── urls.py                      # URL routing for catalog views
│   ├── views.py                     # View controllers (MVT)
│   │
│   ├── services/                    # Decoupled business logic
│   │   ├── search.py                # Unified search with fallback & query logging
│   │   └── semantic_search.py       # Pinecone vector similarity interface
│   │
│   └── management/
│       └── commands/
│           └── seed_data.py         # Seed data generator with 10+ realistic components
│
├── templates/                       # Clean, human-made UI templates
│   ├── base.html                    # Base layout with internal repository header & footer
│   └── components/
│       ├── home.html                # Dashboard with search & recent components
│       ├── component_list.html      # Repository catalog with filter & sort
│       ├── component_detail.html    # Full spec, file download & reuse history
│       ├── component_form.html      # Add & Edit component form
│       ├── component_confirm_delete.html # Deletion confirmation
│       ├── browse.html              # Hierarchical category tree navigation
│       ├── search_results.html      # Search result listings with engine metadata
│       ├── analytics.html           # Usage statistics & query analysis
│       ├── reports.html             # Executive audit report with print & CSV export
│       └── login.html               # Developer authentication
│
├── static/
│   ├── css/
│   │   └── style.css                # Handcrafted developer-internal stylesheet
│   └── js/
│       └── main.js                  # Vanilla JS for modals and dynamic filtering
│
└── media/                           # Uploaded source code and diagram files
    └── components/                  # Component file storage
```

---

## 4. Database Schema (Entities & Relationships)

| Model | Purpose | Key Attributes |
| :--- | :--- | :--- |
| **`Category`** | Hierarchical taxonomy (Parent-Child) | `name`, `slug`, `parent`, `component_type`, `description` |
| **`Component`** | The reusable software asset | `name`, `description`, `component_type`, `category`, `subcategory`, `keywords`, `author`, `version`, `file`, `view_count`, `download_count`, `reuse_count` |
| **`ReuseRecord`** | Audit trail of component reuses | `component`, `user`, `reused_by`, `project_name`, `action`, `notes`, `reused_at` |
| **`SearchQuery`** | Developer search query logs | `query_text`, `timestamp`, `results_count`, `search_mode` |
| **`ComponentUsage`** | Granular engagement logging | `component`, `action_type` (VIEW/DOWNLOAD/REUSE), `user`, `ip_address`, `timestamp` |
| **`ComponentKeyword`** | Indexed tags for fast lookups | `component`, `keyword` |

---

## 5. How to Run Locally

### Prerequisites
* Python 3.12+ (tested up to Python 3.14)
* `uv` package manager installed (`uv --version`)

### Quick Setup

1. **Activate Environment & Apply Migrations:**
   ```powershell
   uv run python manage.py migrate
   ```

2. **Load Realistic Seed Data:**
   ```powershell
   uv run python manage.py seed_data
   ```
   *Creates realistic components (JWT Auth, Email Validation, DB Connection Pool, Binary Search, MVC Blueprint, E-Commerce ERD, etc.), real downloadable code files, reuse logs, and search queries.*

3. **Start the Development Server:**
   ```powershell
   uv run python manage.py runserver
   ```
   Open your browser at: **`http://127.0.0.1:8000/`**

4. **Default Administrator Credentials:**
   * **Username:** `admin`
   * **Password:** `admin123`
   * Accessible at `http://127.0.0.1:8000/admin/`

5. **Run the Automated Test Suite:**
   ```powershell
   uv run python manage.py test
   ```

---

## 6. Multi-Database Architecture (SQLite for Login + Supabase for Catalogue)

The project implements a separated multi-database architecture coordinated by [`components.db_router.DatabaseRouter`](file:///d:/Later%20Projects/SE_Case_Study/components/db_router.py):

```text
Incoming Request
       │
       ▼
[DatabaseRouter]
  ├── 'auth', 'sessions', 'admin' ────► Database: 'default' (Python's built-in SQLite: auth_users.sqlite3)
  └── 'components' (Catalogue)    ────► Database: 'supabase' (Supabase PostgreSQL / Cloud DB)
```

### Advantages:
1. **Security & Independence:** Authentication tokens and user passwords are kept isolated in the local environment or auth microservice database.
2. **Cloud Scalability:** The large component specifications, tags, descriptions, and file metadata reside in the scalable cloud Supabase PostgreSQL cluster.
3. **No Cross-DB Constraint Failures:** Relational links between `ReuseRecord`/`ComponentUsage` and `User` use `db_constraint=False`, preventing cross-database constraint errors while preserving ORM associations.

### Connecting to Live Supabase:
1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Set your Supabase connection string:
   ```env
   SUPABASE_DB_URL=postgresql://postgres.your-ref:your-password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
3. Run migrations on both databases:
   ```powershell
   uv run python manage.py migrate --database=default
   uv run python manage.py migrate --database=supabase
   uv run python manage.py seed_data
   ```

---

## 7. Semantic Search Architecture (Pinecone Preparation)

The search layer is isolated inside `components/services/`:

```text
User Search Query
       ↓
`services/search.py`
       ↓
Checks `is_semantic_search_configured()` in `services/semantic_search.py`
       ├── [If Configured] ──> Generate Embedding Vector ──> Pinecone Similarity Query ──> Retrieve Matching Component IDs ──> Fetch Metadata from DB
       └── [If Offline]    ──> Intelligent Local Fallback Engine (Tokenized scoring + Concept / Domain Synonym expansion)
                                e.g. "secure user login" matches "JWT Authentication Module"
                                e.g. "email checker" matches "Email Validation Utility"
       ↓
Logs Search Query into `SearchQuery` table (Tracks count & 0-result gap)
       ↓
Renders results with search mode indicator
```

### Enabling Pinecone:
In your `.env` file, specify:
```env
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=component-catalog
EMBEDDING_API_KEY=your_embedding_api_key
```

---

## 8. Software Engineering Viva Talking Points

When presenting this project during your viva examination:

1. **Software Reusability Metrics:**
   * Explain how `ReuseRecord` and `ComponentUsage` measure return on investment (ROI). Instead of developers rebuilding authentication or database utilities from scratch, the system records each reuse, quantifying hours saved.
2. **Query Analysis as a Requirements Engineering Tool:**
   * Discuss how the **Zero-Result Queries** table in the Analytics view acts as an automated requirements gathering mechanism: if 15 developers searched for "OAuth2 Google SSO" and found 0 results, the software architecture team knows what asset to build next.
3. **MVT & Services Layer Decoupling:**
   * Point out that vector search and fallback search are separated from `views.py` into `services/search.py`. This follows the Single Responsibility Principle (SRP) and ensures that external API outages (e.g. Pinecone network issue) do not bring down the web application.
4. **Internal Developer Tool Aesthetic:**
   * Emphasize why the UI was deliberately kept clean, functional, and understated: developers need fast page loads, readable documentation, and immediate access to code artifacts without decorative marketing clutter.