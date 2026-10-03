import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth.models import User
from components.models import Category, Component, ReuseRecord, SearchQuery, ComponentUsage


class Command(BaseCommand):
    help = "Populate the database with realistic sample categories, components, reuse records, and search logs."

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")

        # 1. Categories & Subcategories
        # Root Categories
        backend, _ = Category.objects.get_or_create(
            slug='backend',
            defaults={'name': 'Backend', 'description': 'Server-side logic, data access, and API services', 'component_type': 'CODE'}
        )
        frontend, _ = Category.objects.get_or_create(
            slug='frontend',
            defaults={'name': 'Frontend', 'description': 'User interface components, styling, and client-side validation', 'component_type': 'CODE'}
        )
        algorithms, _ = Category.objects.get_or_create(
            slug='algorithms',
            defaults={'name': 'Algorithms', 'description': 'Standard data structure and algorithmic implementations', 'component_type': 'CODE'}
        )
        design, _ = Category.objects.get_or_create(
            slug='design',
            defaults={'name': 'Design', 'description': 'Architectural blueprints, UML diagrams, and entity-relationship models', 'component_type': 'DESIGN'}
        )

        # Subcategories
        # Backend subcategories
        auth_cat, _ = Category.objects.get_or_create(
            slug='authentication',
            defaults={'name': 'Authentication', 'parent': backend, 'description': 'Identity verification and token management'}
        )
        jwt_cat, _ = Category.objects.get_or_create(
            slug='jwt',
            defaults={'name': 'JWT', 'parent': auth_cat, 'description': 'JSON Web Token encoding, decoding, and verification'}
        )
        oauth_cat, _ = Category.objects.get_or_create(
            slug='oauth',
            defaults={'name': 'OAuth', 'parent': auth_cat, 'description': 'OAuth2 authorization flows and provider integration'}
        )

        db_cat, _ = Category.objects.get_or_create(
            slug='database',
            defaults={'name': 'Database', 'parent': backend, 'description': 'Data persistence, ORM utilities, and connection pools'}
        )
        sql_cat, _ = Category.objects.get_or_create(
            slug='sql',
            defaults={'name': 'SQL', 'parent': db_cat, 'description': 'Relational database connection handlers and query builders'}
        )
        mongo_cat, _ = Category.objects.get_or_create(
            slug='mongodb',
            defaults={'name': 'MongoDB', 'parent': db_cat, 'description': 'NoSQL document database adapters and utilities'}
        )

        # Frontend subcategories
        ui_cat, _ = Category.objects.get_or_create(
            slug='ui',
            defaults={'name': 'UI', 'parent': frontend, 'description': 'Reusable HTML/CSS widgets and layout patterns'}
        )
        validation_cat, _ = Category.objects.get_or_create(
            slug='validation',
            defaults={'name': 'Validation', 'parent': frontend, 'description': 'Form and data format validation routines'}
        )

        # Algorithm subcategories
        searching_cat, _ = Category.objects.get_or_create(
            slug='searching',
            defaults={'name': 'Searching', 'parent': algorithms, 'description': 'Search and lookup algorithms'}
        )
        sorting_cat, _ = Category.objects.get_or_create(
            slug='sorting',
            defaults={'name': 'Sorting', 'parent': algorithms, 'description': 'Sorting algorithms and order manipulation'}
        )

        # Design subcategories
        uml_cat, _ = Category.objects.get_or_create(
            slug='uml',
            defaults={'name': 'UML', 'parent': design, 'description': 'Unified Modeling Language class and sequence diagrams'}
        )
        arch_cat, _ = Category.objects.get_or_create(
            slug='architecture',
            defaults={'name': 'Architecture', 'parent': design, 'description': 'System architecture blueprints and patterns'}
        )
        db_design_cat, _ = Category.objects.get_or_create(
            slug='database-design',
            defaults={'name': 'Database Design', 'parent': design, 'description': 'Entity-Relationship (ER) schemas and relational models'}
        )

        self.stdout.write("Categories created.")

        # Create demo users if they don't exist
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@college.edu', 'is_staff': True, 'is_superuser': True}
        )
        if _:
            admin_user.set_password('admin123')
            admin_user.save()

        dev_user, created_dev = User.objects.get_or_create(
            username='developer',
            defaults={'email': 'dev@college.edu', 'first_name': 'Software', 'last_name': 'Engineer'}
        )
        if created_dev:
            dev_user.set_password('dev123')
            dev_user.save()

        # 2. Components with real code / diagram file attachments
        components_data = [
            {
                'name': 'JWT Authentication Module',
                'description': 'A robust, self-contained Python module for generating, signing, and verifying JSON Web Tokens (JWT) using HMAC-SHA256. Includes helper functions for token expiration, payload claim validation, and secure HTTP authorization header parsing.',
                'component_type': 'CODE',
                'category': backend,
                'subcategory': jwt_cat,
                'keywords': 'jwt, auth, authentication, security, token, login, rfc7519',
                'author': 'Alex Rivera (Backend Team)',
                'version': '1.2.0',
                'view_count': 64,
                'download_count': 38,
                'reuse_count': 17,
                'filename': 'jwt_auth_helper.py',
                'file_content': '''"""
JWT Authentication Helper Module
Reusable component for HMAC-SHA256 JWT creation and validation.
"""
import hmac
import hashlib
import base64
import json
import time

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def b64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict, secret: str, expires_in_sec: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = payload.copy()
    payload_copy['exp'] = int(time.time()) + expires_in_sec
    payload_copy['iat'] = int(time.time())

    h_enc = b64url_encode(json.dumps(header).encode('utf-8'))
    p_enc = b64url_encode(json.dumps(payload_copy).encode('utf-8'))
    signing_input = f"{h_enc}.{p_enc}".encode('utf-8')
    
    signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    s_enc = b64url_encode(signature)
    return f"{h_enc}.{p_enc}.{s_enc}"

def verify_jwt(token: str, secret: str) -> dict:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    h_enc, p_enc, s_enc = parts
    signing_input = f"{h_enc}.{p_enc}".encode('utf-8')
    expected_sig = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    actual_sig = b64url_decode(s_enc)
    
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Signature mismatch")
        
    payload = json.loads(b64url_decode(p_enc).decode('utf-8'))
    if 'exp' in payload and time.time() > payload['exp']:
        raise ValueError("Token expired")
    return payload
'''
            },
            {
                'name': 'Email Validation Utility',
                'description': 'A comprehensive input validation utility for verifying whether an email address follows standard RFC 5322 syntax. Checks top-level domains, forbids malicious injection sequences, and strips whitespace.',
                'component_type': 'CODE',
                'category': frontend,
                'subcategory': validation_cat,
                'keywords': 'email, validation, validator, regex, form, checker, syntax',
                'author': 'Sarah Chen (UI/UX Lab)',
                'version': '2.0.1',
                'view_count': 52,
                'download_count': 29,
                'reuse_count': 14,
                'filename': 'email_validator.py',
                'file_content': r'''"""
Email Validation Utility
RFC 5322 compliant regex and heuristic verification.
"""
import re

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

DISALLOWED_DOMAINS = {'tempmail.com', 'throwaway.io', '10minutemail.com'}

def is_valid_email(email: str) -> bool:
    """Returns True if the email is structurally valid and non-disposable."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    if not EMAIL_REGEX.match(email):
        return False
    domain = email.split('@')[-1].lower()
    if domain in DISALLOWED_DOMAINS:
        return False
    return True
'''
            },
            {
                'name': 'Database Connection Utility',
                'description': 'Thread-safe relational database connection manager supporting PostgreSQL, MySQL, and SQLite. Implements automated pooling, retry with exponential backoff on transient connection failures, and clean cursor context managers.',
                'component_type': 'CODE',
                'category': backend,
                'subcategory': sql_cat,
                'keywords': 'database, sql, postgres, connection, pool, retry, sqlite',
                'author': 'David Kumar (Database Admin)',
                'version': '1.1.0',
                'view_count': 48,
                'download_count': 24,
                'reuse_count': 9,
                'filename': 'db_connection_pool.py',
                'file_content': '''"""
Database Connection Utility
Context-managed DB session and query execution.
"""
import sqlite3
from contextlib import contextmanager

class DatabaseConnectionPool:
    def __init__(self, db_path="app.db"):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
'''
            },
            {
                'name': 'Binary Search Implementation',
                'description': 'Optimized binary search routine in Python handling sorted lists with duplicate keys, leftmost and rightmost insertion point detection (bisect), and custom comparator support.',
                'component_type': 'CODE',
                'category': algorithms,
                'subcategory': searching_cat,
                'keywords': 'binary search, algorithm, search, logarithmic, bisect, sorting',
                'author': 'Prof. A. Vance (Algorithms Lab)',
                'version': '1.0.0',
                'view_count': 35,
                'download_count': 16,
                'reuse_count': 8,
                'filename': 'binary_search.py',
                'file_content': '''"""
Binary Search Algorithm Implementation
O(log n) time complexity searching routines.
"""
from typing import List, Any

def binary_search(arr: List[Any], target: Any) -> int:
    """Returns index of target in sorted list `arr`, or -1 if absent."""
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

def binary_search_leftmost(arr: List[Any], target: Any) -> int:
    """Finds the lowest index where target occurs."""
    low, high = 0, len(arr)
    while low < high:
        mid = (low + high) // 2
        if arr[mid] < target:
            low = mid + 1
        else:
            high = mid
    return low if low < len(arr) and arr[low] == target else -1
'''
            },
            {
                'name': 'MVC Architecture Design',
                'description': 'Comprehensive software architecture specification describing Model-View-Controller pattern separation for web applications. Outlines boundaries, DTO protocols, controller action flows, and view templating conventions.',
                'component_type': 'DESIGN',
                'category': design,
                'subcategory': arch_cat,
                'keywords': 'mvc, architecture, design pattern, controller, model, view, blueprint',
                'author': 'Elena Rostova (Systems Architect)',
                'version': '1.0.2',
                'view_count': 41,
                'download_count': 19,
                'reuse_count': 6,
                'filename': 'mvc_architecture_blueprint.txt',
                'file_content': '''============================================================
MVC ARCHITECTURAL BLUEPRINT SPECIFICATION
============================================================
1. Model Layer:
   - Holds core business logic and state invariants.
   - Decoupled from HTTP requests and UI rendering.
   - Interacts with ORM and persistent storage.

2. View Layer:
   - Renders data passed by Controller.
   - Minimal business logic (template loops, conditionals only).
   - Serves HTML, JSON, or CSV formats.

3. Controller Layer:
   - Accepts incoming HTTP request.
   - Performs authorization check and validates input DTO.
   - Invokes Domain Services / Models.
   - Selects appropriate View and passes context payload.

4. Data Flow:
   Client -> Router -> Controller -> Service -> Model -> DB
                      Controller <- Service <- Model <- DB
   Client <- Controller (renders View template with context)
============================================================
'''
            },
            {
                'name': 'E-Commerce ER Diagram',
                'description': 'Detailed Entity-Relationship diagram model covering online store domain: Users, Addresses, Products, Categories, Orders, OrderItems, Payments, and Inventory tracking. Includes foreign key constraints, indexing recommendations, and normalization justification up to 3NF.',
                'component_type': 'DESIGN',
                'category': design,
                'subcategory': db_design_cat,
                'keywords': 'er diagram, erd, database, schema, ecommerce, sql, relational',
                'author': 'Michael O\'Connor (Data Engineering)',
                'version': '2.1.0',
                'view_count': 59,
                'download_count': 33,
                'reuse_count': 11,
                'filename': 'ecommerce_schema.sql',
                'file_content': '''-- E-Commerce Relational Entity Schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    sku VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL
);
'''
            },
            {
                'name': 'User Authentication UML Class Diagram',
                'description': 'Standard UML Class Diagram specification modeling user identity, password encryption service, multi-factor token generator, session manager, and role-based access control (RBAC). Rendered in PlantUML format.',
                'component_type': 'DESIGN',
                'category': design,
                'subcategory': uml_cat,
                'keywords': 'uml, class diagram, authentication, plantuml, rbac, security, design',
                'author': 'Elena Rostova (Systems Architect)',
                'version': '1.0.0',
                'view_count': 37,
                'download_count': 18,
                'reuse_count': 7,
                'filename': 'auth_class_diagram.puml',
                'file_content': '''@startuml
skinparam classAttributeIconSize 0

class User {
  - id: Long
  - username: String
  - passwordHash: String
  - email: String
  - roles: List<Role>
  + verifyPassword(plainText: String): Boolean
  + hasPermission(perm: String): Boolean
}

class Role {
  - id: Integer
  - name: String
  - permissions: List<String>
}

interface ITokenService {
  + generateToken(user: User): String
  + validateToken(token: String): TokenClaims
}

class JwtTokenService implements ITokenService {
  - secretKey: String
  - expirationSeconds: Long
  + generateToken(user: User): String
  + validateToken(token: String): TokenClaims
}

class AuthService {
  - tokenService: ITokenService
  + login(credentials: LoginDTO): AuthResult
  + logout(token: String): Void
}

User "1" *-- "many" Role
AuthService --> ITokenService
AuthService --> User
@enduml
'''
            },
            {
                'name': 'OAuth2 Token Handler',
                'description': 'Authorization code grant exchange utility for handling OAuth2 provider callbacks (Google, GitHub). Manages CSRF state tokens, exchanges authorization code for bearer access token, and refreshes expired tokens.',
                'component_type': 'CODE',
                'category': backend,
                'subcategory': oauth_cat,
                'keywords': 'oauth, oauth2, google, github, sso, token, auth',
                'author': 'Alex Rivera (Backend Team)',
                'version': '1.0.0',
                'view_count': 29,
                'download_count': 14,
                'reuse_count': 5,
                'filename': 'oauth2_handler.py',
                'file_content': '''"""
OAuth2 Grant Handler Utility
"""
import urllib.parse
import json

class OAuth2Client:
    def __init__(self, client_id, client_secret, auth_url, token_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url

    def get_authorization_url(self, redirect_uri: str, state: str, scope: str = 'read') -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': scope,
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"
'''
            },
            {
                'name': 'Merge Sort Algorithm',
                'description': 'Stable divide-and-conquer merge sort algorithm implemented in clean Python. Guaranteed O(n log n) runtime performance with iterative bottom-up variant to minimize recursion stack overhead.',
                'component_type': 'CODE',
                'category': algorithms,
                'subcategory': sorting_cat,
                'keywords': 'sorting, merge sort, divide and conquer, algorithm, array, stable sort',
                'author': 'Prof. A. Vance (Algorithms Lab)',
                'version': '1.0.1',
                'view_count': 31,
                'download_count': 12,
                'reuse_count': 4,
                'filename': 'merge_sort.py',
                'file_content': '''"""
Merge Sort Implementation
Guaranteed O(N log N) stable sorting.
"""
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
'''
            },
            {
                'name': 'Responsive Navigation Bar Component',
                'description': 'Accessible, dependency-free vanilla HTML/CSS responsive navigation header bar with hamburger menu toggle, keyboard tab indexing, ARIA landmarks, and zero external framework requirements.',
                'component_type': 'CODE',
                'category': frontend,
                'subcategory': ui_cat,
                'keywords': 'ui, navigation, navbar, responsive, html, css, header, vanilla js',
                'author': 'Sarah Chen (UI/UX Lab)',
                'version': '1.1.0',
                'view_count': 45,
                'download_count': 22,
                'reuse_count': 8,
                'filename': 'navbar_component.html',
                'file_content': '''<!-- Accessible Responsive Navigation Component -->
<nav class="app-nav" aria-label="Main Navigation">
  <div class="nav-brand">
    <a href="/">Project System</a>
  </div>
  <button class="nav-toggle" aria-expanded="false" aria-label="Toggle navigation">
    <span class="hamburger"></span>
  </button>
  <ul class="nav-menu" id="primary-menu">
    <li><a href="/home/">Home</a></li>
    <li><a href="/components/">Components</a></li>
    <li><a href="/browse/">Browse</a></li>
    <li><a href="/about/">About</a></li>
  </ul>
</nav>
'''
            }
        ]

        self.stdout.write("Seeding components...")
        for data in components_data:
            filename = data.pop('filename')
            file_content = data.pop('file_content')

            component, created = Component.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created or not component.file:
                component.file.save(filename, ContentFile(file_content.encode('utf-8')), save=True)

        self.stdout.write("Components seeded.")

        # 3. Seed Realistic Reuse Records
        jwt_comp = Component.objects.filter(name='JWT Authentication Module').first()
        if jwt_comp and not jwt_comp.reuse_records.exists():
            ReuseRecord.objects.create(
                component=jwt_comp,
                reused_by='Dev Team - Student Portal',
                project_name='Student Portal Authentication Microservice',
                action='Integrated into project',
                notes='Imported JWT verification helper into the API gateway to authenticate incoming student requests.'
            )
            ReuseRecord.objects.create(
                component=jwt_comp,
                reused_by='Priya Sharma (SE Batch 2026)',
                project_name='Hospital Management System',
                action='Forked and adapted',
                notes='Used the HMAC-SHA256 signature logic for doctor authentication tokens.'
            )

        email_comp = Component.objects.filter(name='Email Validation Utility').first()
        if email_comp and not email_comp.reuse_records.exists():
            ReuseRecord.objects.create(
                component=email_comp,
                reused_by='Karthik Rajan',
                project_name='Campus Event Registration Portal',
                action='Integrated into project',
                notes='Added as form validation middleware for participant registration emails.'
            )

        er_comp = Component.objects.filter(name='E-Commerce ER Diagram').first()
        if er_comp and not er_comp.reuse_records.exists():
            ReuseRecord.objects.create(
                component=er_comp,
                reused_by='Architecture Group 4',
                project_name='Online Bookstore Case Study',
                action='Adopted schema design',
                notes='Reused database tables for users, orders, and products with minor modifications.'
            )

        # 4. Seed Realistic Search Queries for Analytics
        sample_queries = [
            ("jwt auth", 1, 'keyword'),
            ("secure user login", 1, 'keyword'),
            ("database connection", 1, 'keyword'),
            ("email checker", 1, 'keyword'),
            ("binary search", 1, 'keyword'),
            ("uml diagram", 2, 'keyword'),
            ("mvc architecture", 1, 'keyword'),
            ("blockchain smart contract", 0, 'keyword'),
            ("microservices kubernetes helm", 0, 'keyword'),
            ("quantum key distribution", 0, 'keyword'),
            ("sorting algorithm", 1, 'keyword'),
        ]

        if SearchQuery.objects.count() < 10:
            for q_text, count, mode in sample_queries:
                SearchQuery.objects.create(
                    query_text=q_text,
                    results_count=count,
                    search_mode=mode
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded complete sample dataset!"))
