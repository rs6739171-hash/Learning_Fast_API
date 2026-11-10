# Learning FastAPI: Complete Architecture & Concept Guide 🚀

> **Overview**: This project is a production-structured asynchronous RESTful API built with **FastAPI**, **SQLModel**, **PostgreSQL (via Supabase)**, and **JWT (JSON Web Token) OAuth2 Authentication**.
>
> If you built this project by "vibecoding" along with a tutorial, this guide is designed to deconstruct the **logic**, **architecture**, **design patterns**, and **concepts** behind every line of code.

---

## Table of Contents
1. [Core Technologies & Libraries](#1-core-technologies--libraries)
2. [Project Architecture & Directory Tour](#2-project-architecture--directory-tour)
3. [Key Concepts Explained Simply](#3-key-concepts-explained-simply)
   - [Asynchronous Python (`async` / `await`)](#asynchronous-python-async--await)
   - [Dependency Injection (`Depends`)](#dependency-injection-depends)
   - [Database ORM vs Pydantic Schemas](#database-orm-vs-pydantic-schemas)
   - [Password Hashing with Bcrypt](#password-hashing-with-bcrypt)
   - [Authentication with JWT & OAuth2](#authentication-with-jwt--oauth2)
4. [Request & Data Flow Walkthroughs](#4-request--data-flow-walkthroughs)
   - [Flow 1: Seller Registration (`POST /seller/signup`)](#flow-1-seller-registration)
   - [Flow 2: Seller Login (`POST /seller/login`)](#flow-2-seller-login)
   - [Flow 3: Protected Dashboard Access (`GET /seller/dashboard`)](#flow-3-protected-dashboard-access)
   - [Flow 4: Product CRUD Operations (`/product/`)](#flow-4-product-crud-operations)
5. [Common Pitfalls & Lessons Learned](#5-common-pitfalls--lessons-learned)
6. [Local Setup & Running the Server](#6-local-setup--running-the-server)
7. [API Reference Summary](#7-api-reference-summary)

---

## 1. Core Technologies & Libraries

| Technology | Role in This Project |
| :--- | :--- |
| **FastAPI** | High-performance ASGI web framework providing URL routing, request validation, response serialization, and automatic OpenAPI documentation (`/docs`). |
| **SQLModel** | A library created by Tiangolo (the creator of FastAPI) combining **SQLAlchemy** (database operations) and **Pydantic** (data validation) so you write models once. |
| **SQLAlchemy + Asyncpg** | Asynchronous database driver enabling non-blocking database queries to PostgreSQL. |
| **Pydantic (v2) + Pydantic-Settings** | Enforces strict data types for incoming HTTP requests and reads configuration safely from `.env`. |
| **Passlib (with Bcrypt)** | Industrial-grade cryptographic one-way hashing for secure user passwords. |
| **PyJWT** | Encodes and decodes digitally signed JSON Web Tokens for stateless user authentication. |
| **Uvicorn / FastAPI CLI** | ASGI server that executes asynchronous Python code and hot-reloads on file changes. |
| **uv** | Ultra-fast Python package and project manager used for dependency management and running the app. |

---

## 2. Project Architecture & Directory Tour

This codebase uses the **Layered Service Pattern** (Separation of Concerns). Instead of dumping database queries, business logic, and routing into a single file, each responsibility lives in its own dedicated layer:

```text
Learning_Fast_API/
├── .env                         # Secrets & database connection credentials
├── pyproject.toml               # Project configuration, dependencies, and FastAPI entrypoint
├── uv.lock                      # Exact locked versions of dependencies
├── README.md                    # Project documentation & architecture guide
└── app/                         # Main application package
    ├── __init__.py              # Package marker
    ├── main.py                  # FastAPI app factory, lifespan startup & router registration
    ├── config.py                # Environment configuration loaded via Pydantic BaseSettings
    ├── sessions.py              # Async database engine, session generator, and table setup
    ├── models.py                # Re-export bridge for database models
    ├── utils.py                 # Security helpers (JWT token creation & decoding)
    ├── core/
    │   ├── __init__.py
    │   └── security.py          # OAuth2 scheme definition (OAuth2PasswordBearer)
    ├── database/
    │   ├── __init__.py
    │   └── models.py            # SQLModel table definitions (Seller, Product)
    ├── services/
    │   ├── __init__.py
    │   ├── product.py           # ProductService: DB queries for products
    │   └── seller.py            # SellerService: DB queries, password hashing & verification
    └── api/
        ├── master_router.py     # Aggregates sub-routers (sellers, products)
        ├── dependencies.py      # Dependency injection providers (SessionDep, ServiceDep)
        ├── routers/
        │   ├── product.py       # HTTP route handlers for /product endpoints
        │   └── sellers.py       # HTTP route handlers for /seller endpoints
        └── schema/
            ├── product.py       # Pydantic schemas for Seller (Create, Read)
            └── schemas_fields.py# Pydantic schemas & enums for Products (Create, Update, Read)
```

### Detailed Layer Breakdown

#### 1. Configuration Layer (`app/config.py`)
- Reads `.env` using `pydantic-settings`.
- Protects database connection strings by properly URL-encoding special characters (like `@` and `%`) in passwords with `quote_plus`.
- Manages two setting objects: `db_settings` (database credentials) and `security_settings` (JWT secret key & algorithm).

#### 2. Database & Session Layer (`app/sessions.py` & `app/database/models.py`)
- Sets up an **asynchronous engine** (`create_async_engine`) connected to PostgreSQL via `postgresql+asyncpg://`.
- Provides an `async_session` generator (`get_session`) yielding isolated database sessions for requests.
- Contains a `create_db_tables()` function called during FastAPI application startup (`lifespan`) to ensure database tables exist.

#### 3. Data Schema Layer (`app/api/schema/`)
- Defines what the client is **allowed to send** and **allowed to receive**.
- For example, `SellerCreate` requires `password`, while `SellerRead` only exposes `id`, `name`, and `email` to prevent exposing password hashes.

#### 4. Service Layer (`app/services/`)
- Contains **pure business logic**. Routers do not talk directly to the database; they ask Services to fetch, calculate, or save data.
- `ProductService`: Handles `get`, `add`, `update`, `delete`.
- `SellerService`: Handles `add` (hashes password before insert), `get`, and `login` (verifies password and creates tokens).

#### 5. Dependency Layer (`app/api/dependencies.py`)
- Glues the database session and service layers together using FastAPI's `Depends()`.
- Provides clean type aliases: `SessionDep`, `ProductDep`, and `SellerDep`.

#### 6. Router Layer (`app/api/routers/`)
- Defines HTTP paths (`GET`, `POST`, `PATCH`, `DELETE`), response status codes, and input/output contracts.
- Injects dependencies (`service: SellerDep`, `session: SessionDep`) and delegates heavy lifting to services.

---

## 3. Key Concepts Explained Simply

### Asynchronous Python (`async` / `await`)
In traditional synchronous Python, when your code asks a database for a record:
1. The entire server thread blocks and does nothing while waiting for PostgreSQL to reply over the network.
2. No other user can be served during that time.

With `async` and `await`:
```python
result = await self.session.execute(...)
```
When Python hits `await`, it releases the thread back to the event loop. While PostgreSQL processes the query, the server can handle dozens of requests from other users simultaneously.

### Dependency Injection (`Depends`)
Dependency Injection is an architectural pattern where a function receives the objects it needs from the outside rather than creating them manually inside.

In FastAPI:
```python
@router.post("/signup")
async def register_seller(seller: SellerCreate, service: SellerDep):
    return await service.add(seller)
```
You don't manually create the database connection or instantiate `SellerService`. FastAPI automatically:
1. Calls `get_session()` to create a database session.
2. Passes that session into `SellerService(session)`.
3. Injects that initialized service directly into `register_seller`.
4. Closes the database session when the request finishes.

### Database ORM vs Pydantic Schemas
A common beginner question is: *"Why do we have both `models.py` and `schema/product.py`?"*

- **SQLModel Table Models (`app/database/models.py`)**:
  - Decorated with `table=True`.
  - Represent the **actual database tables and columns** in PostgreSQL.
  - Contain internal fields like `password_hash`.
- **Pydantic Schema Models (`app/api/schema/`)**:
  - Represent the **HTTP API contract**.
  - `ProductCreate`: Fields required when creating a product.
  - `ProductUpdate`: Optional fields for partial updates (`PATCH`).
  - `SellerRead`: What is sent back to the browser (never includes passwords!).

### Password Hashing with Bcrypt
Passwords are **never stored in plain text**.
1. When a user signs up with password `"secret123"`, `pwd_context.hash("secret123")` generates a cryptographically salted one-way hash (e.g. `$2b$12$...`).
2. When the user logs in, `pwd_context.verify("secret123", seller.password_hash)` checks if the entered password matches the hash.
3. Even if the database is leaked, the attacker cannot reverse the hash into the actual password.

### Authentication with JWT & OAuth2
This project implements the **OAuth2 Password Flow** with **Bearer JWT Tokens**:
1. **Client** sends username (email) and password to `/seller/login`.
2. **Server** validates credentials and signs a JSON object (payload) using `SECRET_KEY` and the `HS256` algorithm:
   ```json
   {
     "user": { "id": 1, "name": "Ali", "email": "ali@gmail.com" },
     "exp": 1794343529
   }
   ```
3. **Client** receives this token string and sends it on every protected request in the HTTP header:
   ```http
   Authorization: Bearer <token_string>
   ```
4. **Server** verifies the digital signature. Because only the server knows the secret key, nobody can tamper with the data inside the token.

---

## 4. Request & Data Flow Walkthroughs

### Flow 1: Seller Registration
```
Client (POST /seller/signup with JSON body)
  │
  ▼
app/api/routers/sellers.py: register_seller()
  │  [Validates body against SellerCreate schema]
  ▼
app/services/seller.py: SellerService.add()
  │  [Hashes password with bcrypt -> password_hash]
  │  [Creates Seller SQLModel instance]
  ▼
app/sessions.py: session.add() -> session.commit()
  │  [INSERT INTO sellers ... in PostgreSQL]
  ▼
Returns SellerRead schema to Client (password is excluded)
```

### Flow 2: Seller Login
```
Client (POST /seller/login with form data username & password)
  │
  ▼
app/api/routers/sellers.py: login()
  │  [Receives OAuth2PasswordRequestForm dependency]
  ▼
app/services/seller.py: SellerService.login()
  │  [SELECT * FROM sellers WHERE email = username]
  │  [Verifies password using pwd_context.verify()]
  │  [Generates signed JWT via app/utils.py: generate_access_token()]
  ▼
Returns: {"access_token": "<jwt>", "token_type": "bearer"}
```

### Flow 3: Protected Dashboard Access
```
Client (GET /seller/dashboard with Header: "Authorization: Bearer <token>")
  │
  ▼
app/core/security.py: oauth2_scheme
  │  [Extracts bearer token from header; returns 401 if missing]
  ▼
app/api/routers/sellers.py: get_dashboard()
  │
  ▼
app/utils.py: decode_access_token()
  │  [Verifies JWT signature and checks expiry timestamp]
  │  [Returns decoded payload dict or None if invalid]
  ▼
app/services/seller.py: SellerService.get(user_id)
  │  [SELECT * FROM sellers WHERE id = user_id]
  ▼
Returns Seller profile JSON to Client
```

### Flow 4: Product CRUD Operations
- **`POST /product/`**: Creates product with automatic `ProductStatus.active` and 1-year `warranty_until` timestamp.
- **`GET /product/?id=1`**: Fetches product by ID or raises HTTP 404.
- **`PATCH /product/?id=1`**: Uses `product_update.model_dump(exclude_none=True)` so only supplied fields are updated, preventing accidental overwrites with `null`.
- **`DELETE /product/?id=1`**: Removes product from database and returns confirmation message.

---

## 5. Common Pitfalls & Lessons Learned

During the development and debugging of this application, several real-world engineering issues were identified and resolved:

1. **Circular Imports**:
   - *Problem*: `sellers.py` imported `decode_access_token` from `utils.py`, while `utils.py` imported `from app.api.routers import sellers`.
   - *Solution*: Utility modules should be self-contained and should not import routers or higher-level business components.
2. **`OAuth2PasswordRequestForm` Dependency**:
   - *Problem*: Writing `request_form: OAuth2PasswordRequestForm` causes FastAPI to treat it as a JSON body, triggering `FastAPIError: Invalid args for response field`.
   - *Solution*: Form classes must be injected with `= Depends()`.
3. **Special Characters in PostgreSQL URL**:
   - *Problem*: Passwords containing `@` or `%` break URL parsers if concatenated directly (`postgresql://user:pass@host/db`).
   - *Solution*: Always wrap password variables with `urllib.parse.quote_plus()`.
4. **Service vs Session Dependency Confusion**:
   - *Problem*: Calling `await session.get(...)` when `session` was injected as `SellerDep` failed with `AttributeError: 'SellerService' object has no attribute 'get'`.
   - *Solution*: Implement proper query methods on the service class so the router never depends on raw database internals.
5. **Lifespan Context Manager**:
   - *Problem*: Initializing tables inside `lifespan` requires `async with engine.begin()`, and `create_all` must be passed as a function reference without parentheses (`run_sync(SQLModel.metadata.create_all)`).

---

## 6. Local Setup & Running the Server

### Prerequisites
- Python 3.12+
- `uv` package manager (or standard `pip`)

### 1. Configure Environment Variables
Create a `.env` file in the project root:
```env
DATABSE_URL=postgresql://postgres.<user>:<password>@<host>:5432/postgres
POSTGRES_SERVER=<host>
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.<user>
POSTGRES_PASSWORD=<your_password>

JWT_SECRET=YOUR_SUPER_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
```

### 2. Install Dependencies
```bash
uv sync
# OR
pip install -e .
```

### 3. Run the Development Server
```bash
uv run fastapi dev
# OR
.venv\Scripts\fastapi dev
```

### 4. Interactive Documentation
Once the server starts, open your browser:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 7. API Reference Summary

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/seller/signup` | ❌ No | Registers a new seller account. Returns `SellerRead`. |
| `POST` | `/seller/login` | ❌ No | OAuth2 password login. Returns access token and bearer type. |
| `GET` | `/seller/dashboard` | 🔒 **Yes (Bearer)** | Returns profile data of the currently authenticated seller. |
| `GET` | `/product/?id={id}` | ❌ No | Fetches a product by its numeric ID. |
| `POST` | `/product/` | ❌ No | Creates a new product with default status and warranty. |
| `PATCH` | `/product/?id={id}` | ❌ No | Partially updates existing product fields. |
| `DELETE` | `/product/?id={id}` | ❌ No | Deletes a product by ID. |

