# Face Payment System — Implementation Plan

## Overview

Two apps in one Spring Boot project:
1. **Bank App** — user registration, bank account, face payment activation
2. **Store App** — product catalog, orders, checkout using face payment

Both apps share the same database and Spring Boot instance for easy testing.

**Stack:**
- Java Spring Boot 3.x (REST API)
- PostgreSQL (database)
- Python FastAPI (face service — runs on same machine)
- OpenCV + DeepFace MiniFASNet (anti-spoofing + recognition)

---

## System Architecture

```
[Client / Mobile App]
        ↓ HTTP
[Spring Boot REST API :8080]
        ↓ HTTP (localhost)
[Python FastAPI Face Service :8000]
        ↓
[Camera + OpenCV + DeepFace]
        ↓
[face_dataset/{user_id}.npy]

[Spring Boot] ←→ [PostgreSQL :5432]
```

All services run on the same machine (or same Docker network later).

---

## User Journey

```
[BANK APP]
1. REGISTER
   User fills: name, email, phone, account type, initial balance
   → Bank account created
   → face_payment status = INACTIVE

2. ACTIVATE FACE PAYMENT
   User opens camera → face data collected + saved
   → face_payment status = ACTIVE

[STORE APP]
3. BROWSE PRODUCTS
   User sees product list with name, price, stock

4. CHECKOUT WITH FACE
   User picks product + quantity
   → App checks balance
   → Camera opens → anti-spoof + face match
   → If match → order confirmed + balance deducted
   → If fake/mismatch → order rejected
```

---

## Phase 1: Database Design (PostgreSQL)

### Tables

```sql
-- 1. users
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    phone         VARCHAR(20),
    created_at    TIMESTAMP DEFAULT NOW()
);

-- 2. bank_accounts
CREATE TABLE bank_accounts (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT REFERENCES users(id),
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type   VARCHAR(20) NOT NULL,   -- SAVINGS or CHECKING
    balance        DECIMAL(15,2) DEFAULT 0,
    created_at     TIMESTAMP DEFAULT NOW()
);

-- 3. face_payment
CREATE TABLE face_payment (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT REFERENCES users(id) UNIQUE,
    file_path     VARCHAR(255),            -- face_dataset/{user_id}.npy
    status        VARCHAR(20) DEFAULT 'INACTIVE', -- INACTIVE | ACTIVE
    activated_at  TIMESTAMP,
    created_at    TIMESTAMP DEFAULT NOW()
);
```

### Account Number Generation
- Format: `FP` + userId padded + random 6 digits → e.g. `FP00101982341`

---

## Phase 2: Python FastAPI Face Service

### File: `face_service.py`

#### POST `/enroll`
```
Request:  { "user_id": 101 }
Action:   Opens camera → collects 100 face frames (every 10th frame)
          → saves to face_dataset/101.npy
Response: { "success": true, "user_id": 101 }
```

#### POST `/verify`
```
Request:  { "user_id": 101 }
Action:   Loads face_dataset/101.npy
          → Opens camera → anti-spoof check (DeepFace MiniFASNet)
          → KNN face match against 101.npy
Response: { "match": true/false, "user_id": 101, "score": 0.95 }
```

- Runs on `localhost:8000`
- Spring Boot calls it via HTTP (RestTemplate)
- Camera must be available on same machine
- `face_dataset/` folder shared between `face_service.py` and `face_recognition.py`

---

## Phase 2b: Store Database Tables

```sql
-- 4. products
CREATE TABLE products (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    price       DECIMAL(15,2) NOT NULL,
    stock       INT DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 5. orders
CREATE TABLE orders (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT REFERENCES users(id),
    total_amount   DECIMAL(15,2) NOT NULL,
    status         VARCHAR(20) DEFAULT 'PENDING', -- PENDING | SUCCESS | FAILED
    created_at     TIMESTAMP DEFAULT NOW()
);

-- 6. order_items
CREATE TABLE order_items (
    id          BIGSERIAL PRIMARY KEY,
    order_id    BIGINT REFERENCES orders(id),
    product_id  BIGINT REFERENCES products(id),
    quantity    INT NOT NULL,
    price       DECIMAL(15,2) NOT NULL  -- snapshot price at time of order
);
```

### Sample Seed Data (for testing)
```sql
INSERT INTO products (name, description, price, stock) VALUES
  ('Coffee',      'Arabica black coffee',  25000,  50),
  ('Sandwich',    'Chicken sandwich',      35000,  30),
  ('Mineral Water','500ml mineral water',  10000, 100),
  ('Laptop Stand','Aluminium laptop stand',150000,  20);
```

---

## Phase 3: Spring Boot Project Structure

```
face-payment/
├── pom.xml
└── src/main/java/com/facepayment/
    ├── FacePaymentApplication.java
    │
    ├── bank/                            ← BANK MODULE
    │   ├── entity/
    │   │   ├── User.java
    │   │   ├── BankAccount.java
    │   │   └── FacePayment.java
    │   ├── repository/
    │   │   ├── UserRepository.java
    │   │   ├── BankAccountRepository.java
    │   │   └── FacePaymentRepository.java
    │   ├── dto/
    │   │   ├── request/
    │   │   │   ├── RegisterRequest.java
    │   │   │   └── PaymentRequest.java
    │   │   └── response/
    │   │       ├── RegisterResponse.java
    │   │       ├── ActivateFaceResponse.java
    │   │       └── PaymentResponse.java
    │   ├── service/
    │   │   ├── UserService.java
    │   │   ├── BankAccountService.java
    │   │   ├── FaceService.java        ← calls Python API
    │   │   └── PaymentService.java
    │   └── controller/
    │       ├── UserController.java
    │       ├── FaceController.java
    │       └── PaymentController.java
    │
    ├── store/                           ← STORE MODULE
    │   ├── entity/
    │   │   ├── Product.java
    │   │   ├── Order.java
    │   │   └── OrderItem.java
    │   ├── repository/
    │   │   ├── ProductRepository.java
    │   │   ├── OrderRepository.java
    │   │   └── OrderItemRepository.java
    │   ├── dto/
    │   │   ├── request/
    │   │   │   └── CheckoutRequest.java
    │   │   └── response/
    │   │       ├── ProductResponse.java
    │   │       └── OrderResponse.java
    │   ├── service/
    │   │   ├── ProductService.java
    │   │   └── OrderService.java       ← calls PaymentService internally
    │   └── controller/
    │       ├── ProductController.java
    │       └── OrderController.java
    │
    └── common/
        └── ApiResponse.java            ← shared response wrapper
```

### Dependencies (pom.xml)
- `spring-boot-starter-web`
- `spring-boot-starter-data-jpa`
- `postgresql` driver
- `lombok`
- `spring-boot-starter-validation`

---

## Phase 4: REST API Endpoints

### User Controller `/api/users`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register` | Register user + bank account |
| GET | `/api/users/{id}` | Get user profile + face payment status |

### Face Controller `/api/face`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/face/activate/{userId}` | Activate face payment (enroll face) |
| GET | `/api/face/status/{userId}` | Check face payment status |

### Payment Controller `/api/payment`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payment/pay` | Verify face then process payment |

### Store — Product Controller `/api/store/products`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/store/products` | List all available products |
| GET | `/api/store/products/{id}` | Get product detail |
| POST | `/api/store/products` | Add new product (admin/seed) |

### Store — Order Controller `/api/store/orders`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/store/orders/checkout` | Place order + face payment |
| GET | `/api/store/orders/{userId}` | Get order history for user |

---

## Phase 5: Step 1 — Bank Registration Flow

```
Client → POST /api/users/register
Body:
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "08123456789",
  "account_type": "SAVINGS",
  "initial_balance": 1000000
}

Steps:
1. Validate request
2. Save User to DB → get user.id = 101
3. Generate account_number → Save BankAccount to DB
4. Create FacePayment record with status = INACTIVE
5. Return response

Response:
{
  "user_id": 101,
  "full_name": "John Doe",
  "account_number": "FP00101982341",
  "account_type": "SAVINGS",
  "balance": 1000000,
  "face_payment_status": "INACTIVE"
}
```

---

## Phase 6: Step 2 — Activate Face Payment Flow

```
Client → POST /api/face/activate/101

Steps:
1. Check user exists in DB
2. Check face_payment status — if already ACTIVE return error
3. Call Python POST /enroll { user_id: 101 }
   → Python opens camera
   → User looks at camera for ~10 seconds
   → Face saved as face_dataset/101.npy
4. Update face_payment:
   - file_path = "face_dataset/101.npy"
   - status = ACTIVE
   - activated_at = NOW()
5. Return response

Response (success):
{
  "user_id": 101,
  "face_payment_status": "ACTIVE",
  "message": "Face payment activated successfully."
}

Response (already active):
{
  "status": "ERROR",
  "message": "Face payment already activated for this user."
}
```

---

## Phase 7: Step 3 — Payment with Face Verification Flow

```
Client → POST /api/payment/pay
Body:
{
  "user_id": 101,
  "amount": 50000,
  "description": "Payment for order #99"
}

Steps:
1. Load user + bank account from DB
2. Check face_payment status = ACTIVE (else reject)
3. Check balance >= amount (else reject)
4. Call Python POST /verify { user_id: 101 }
   → Python loads face_dataset/101.npy
   → Opens camera → anti-spoof check (DeepFace)
   → KNN match
   → Returns { match: true, score: 0.97 }
5. If match = true  → deduct balance → return SUCCESS
6. If match = false → return FACE_MISMATCH (no deduction)

Response (success):
{
  "status": "SUCCESS",
  "user_id": 101,
  "amount": 50000,
  "remaining_balance": 950000,
  "description": "Payment for order #99"
}

Response (face fail):
{
  "status": "FACE_MISMATCH",
  "message": "Face verification failed. Transaction rejected."
}

Response (face payment not active):
{
  "status": "ERROR",
  "message": "Face payment is not activated. Please activate first."
}
```

---

## Phase 7b: Store Checkout Flow

```
Client → POST /api/store/orders/checkout
Body:
{
  "user_id": 101,
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}

Steps in Spring Boot (OrderService):
1. Validate all products exist + have enough stock
2. Calculate total:
   Coffee x2 = 50,000 + Water x1 = 10,000 → total = 60,000
3. Check user balance >= 60,000
4. Check face_payment status = ACTIVE
5. Call Python POST /verify { user_id: 101 }
   → Camera opens → anti-spoof + face match
6. If match = true:
   → Deduct balance (60,000) from bank_account
   → Reduce product stock
   → Save Order (status=SUCCESS) + OrderItems
   → Return order summary
7. If match = false:
   → Save Order (status=FAILED)
   → Return FACE_MISMATCH error

Response (success):
{
  "status": "SUCCESS",
  "order_id": 55,
  "items": [
    { "product": "Coffee",        "qty": 2, "subtotal": 50000 },
    { "product": "Mineral Water", "qty": 1, "subtotal": 10000 }
  ],
  "total_amount": 60000,
  "remaining_balance": 940000
}

Response (face fail):
{
  "status": "FACE_MISMATCH",
  "message": "Face verification failed. Order rejected."
}
```

---

## Phase 8: FaceService.java (Spring → Python HTTP)

```java
@Service
public class FaceService {

    @Value("${face.service.url}")
    private String pythonBaseUrl;

    private final RestTemplate restTemplate;

    // POST localhost:8000/enroll → { user_id }
    public boolean enrollFace(Long userId) { ... }

    // POST localhost:8000/verify → { user_id }
    // returns FaceVerifyResult { match, score }
    public FaceVerifyResult verifyFace(Long userId) { ... }
}
```

---

## Phase 9: Error Handling

| Scenario | HTTP Status | Status Field |
|----------|-------------|--------------|
| Email already registered | 400 | EMAIL_EXISTS |
| User not found | 404 | USER_NOT_FOUND |
| Face already activated | 400 | FACE_ALREADY_ACTIVE |
| Face not yet activated | 400 | FACE_NOT_ACTIVE |
| Face enrollment failed (camera) | 500 | ENROLL_FAILED |
| Face mismatch on payment | 403 | FACE_MISMATCH |
| Insufficient balance | 400 | INSUFFICIENT_BALANCE |

---

## Phase 10: application.properties

```properties
# PostgreSQL
spring.datasource.url=jdbc:postgresql://localhost:5432/facepaymentdb
spring.datasource.username=postgres
spring.datasource.password=yourpassword
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true

# Python Face Service
face.service.url=http://localhost:8000

# Server
server.port=8080
```

---

## Phase 11: Deployment

### Same Machine — for testing
```
Terminal 1:  python3 face_service.py        # :8000
Terminal 2:  ./mvnw spring-boot:run         # :8080
PostgreSQL:  running as service on :5432
```

### Docker Compose — for production
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: facepaymentdb
      POSTGRES_PASSWORD: yourpassword
    ports: ["5432:5432"]

  face-service:
    build: ./python
    ports: ["8000:8000"]
    devices:
      - /dev/video0:/dev/video0    # camera access

  spring-app:
    build: ./face-payment
    ports: ["8080:8080"]
    depends_on: [postgres, face-service]
```

---

## Implementation Order (Checklist)

### Bank App
- [ ] Phase 1  — Create PostgreSQL database `facepaymentdb` + all tables
- [ ] Phase 2  — Build `face_service.py` (FastAPI `/enroll` + `/verify`)
- [ ] Phase 3  — Create Spring Boot project `face-payment` + pom.xml
- [ ] Phase 4  — Create bank entities: User, BankAccount, FacePayment
- [ ] Phase 5  — Create bank repositories + services
- [ ] Phase 6  — Create FaceService.java (HTTP client to Python)
- [ ] Phase 7  — Create UserController (register)
- [ ] Phase 8  — Create FaceController (activate face payment)
- [ ] Phase 9  — Create PaymentController (direct bank payment)

### Store App
- [ ] Phase 10 — Create store entities: Product, Order, OrderItem
- [ ] Phase 11 — Create store repositories + ProductService + OrderService
- [ ] Phase 12 — Create ProductController (list/add products)
- [ ] Phase 13 — Create OrderController (checkout with face)
- [ ] Phase 14 — Seed sample products into DB

### Testing
- [ ] Phase 15 — Test full flow:
                  register → activate face → browse products → checkout → verify face
- [ ] Phase 16 — Docker Compose setup (later)
