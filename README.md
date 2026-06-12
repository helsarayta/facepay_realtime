# Face Payment System

A banking payment system that uses real-time face recognition with anti-spoofing (liveness detection) to authorize transactions. All API endpoints are secured with JWT authentication.

---

## System Requirements

- Python 3.11
- Java 17
- Maven 3.x
- Docker

---

## Project Structure

```
Real-time-Face-Recognition-Project/
├── face_service.py                  ← Python FastAPI face service (port 8000)
├── face_recognition.py              ← Standalone face recognition demo
├── face_data.py                     ← Standalone face enrollment demo
├── face_dataset/                    ← Stored face data (.npy files)
├── haarcascade_frontalface_alt.xml  ← Face detection model
└── face-payment/                    ← Spring Boot app (port 8080)
    ├── pom.xml
    └── src/main/
        ├── java/com/facepayment/
        │   ├── auth/                ← JWT filter, UserDetailsService
        │   ├── bank/                ← User, BankAccount, FacePayment
        │   ├── store/               ← Product, Order, OrderItem
        │   └── config/              ← SecurityConfig, AppConfig
        └── resources/
            └── application.properties
```

---

## How It Works

```
Client (curl / Postman)
        ↓  JWT Token required
Spring Boot :8080  ←→  PostgreSQL :5432
        ↓
Python Face Service :8000
        ↓
Camera → DeepFace Anti-Spoof + KNN Match
```

---

## Authentication

All API endpoints require a JWT token **except**:
- `POST /api/users/register`
- `POST /api/auth/login`

Include the token in every request header:
```
Authorization: Bearer <your_token>
```

Token is valid for **24 hours**.

---

## Option A — Run with Docker Compose (Recommended)

Run all services with a single command.

> **macOS camera note:** Docker on macOS cannot access the host camera. The `face-service` (which needs the camera for enrollment and verification) must run natively on macOS. Use Option B below for the face service and Docker Compose only for postgres + springboot.

### On Linux (full Docker Compose)

```bash
cd /path/to/Real-time-Face-Recognition-Project
docker compose up --build
```

All 3 services start automatically:
- PostgreSQL on `:5432`
- Python face service on `:8000`
- Spring Boot on `:8080`

Stop everything:
```bash
docker compose down
```

Stop and delete database data:
```bash
docker compose down -v
```

### On macOS (Docker Compose for postgres + springboot only)

**1.** Comment out the `face-service` block in `docker-compose.yml`:
```yaml
# face-service:
#   build: ...
```

Also update the `springboot` depends_on to remove `face-service`:
```yaml
depends_on:
  postgres:
    condition: service_healthy
```

**2.** Start postgres + springboot:
```bash
docker compose up --build
```

**3.** Run face service natively in a separate terminal:
```bash
cd /path/to/Real-time-Face-Recognition-Project
python3 face_service.py
```

---

## Option B — Run Manually (Step by Step)

---

## Step 1 — Start PostgreSQL (Docker)

```bash
# First time only — creates the container
docker run -d \
  --name facepayment-postgres \
  -e POSTGRES_DB=facepaymentdb \
  -e POSTGRES_USER=facepayment \
  -e POSTGRES_PASSWORD=facepayment123 \
  -p 5432:5432 \
  postgres:15

# From second time onwards — just start the existing container
docker start facepayment-postgres
```

Verify it is running:
```bash
docker exec facepayment-postgres pg_isready -U facepayment -d facepaymentdb
```

Expected output: `/var/run/postgresql:5432 - accepting connections`

---

## Step 2 — Start Python Face Service

Open a new terminal, go to the project folder:

```bash
cd /path/to/Real-time-Face-Recognition-Project
python3 face_service.py
```

Expected output:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> **Note:** Keep this terminal open. The camera will open automatically when enrollment or verification is triggered.

---

## Step 3 — Start Spring Boot

Open another new terminal:

```bash
cd /path/to/Real-time-Face-Recognition-Project/face-payment
JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn spring-boot:run
```

Expected output:
```
Started FacePaymentApplication in X seconds
```

> **Note:** First run will download Maven dependencies (~2 minutes). Subsequent runs are faster.

---

## Step 4 — Register a Bank User

> No token required for this endpoint.

```bash
curl -X POST http://localhost:8080/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "fullName": "Your Name",
    "email": "your@email.com",
    "phone": "08123456789",
    "accountType": "SAVINGS",
    "initialBalance": 5000000,
    "password": "yourpassword"
  }'
```

Expected response:
```json
{
  "status": "SUCCESS",
  "data": {
    "userId": 1,
    "fullName": "Your Name",
    "accountNumber": "FP00001XXXXXX",
    "balance": 5000000,
    "facePaymentStatus": "INACTIVE"
  }
}
```

> Note down the `userId` — you will need it for the next steps.

---

## Step 5 — Login and Get JWT Token

> No token required for this endpoint.

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"
  }'
```

Expected response:
```json
{
  "status": "SUCCESS",
  "message": "Login successful",
  "data": {
    "token": "eyJhbGciOiJIUzM4NCJ9...",
    "type": "Bearer",
    "userId": 1,
    "fullName": "Your Name",
    "email": "your@email.com"
  }
}
```

> **Copy the `token` value** — include it in all subsequent requests as:
> `Authorization: Bearer eyJhbGciOiJIUzM4NCJ9...`

Wrong credentials returns:
```json
{ "status": "INVALID_CREDENTIALS", "message": "Invalid email or password" }
```

---

## Step 6 — Activate Face Payment (Enroll Face)

> Requires token.

```bash
curl -X POST http://localhost:8080/api/face/activate/1 \
  -H "Authorization: Bearer <your_token>"
```

**What happens:**
1. A camera window labelled **"Face Enrollment"** will open
2. Look directly at the camera
3. A green progress bar fills up as 100 face frames are collected (~10 seconds)
4. Window closes automatically when done

Expected response:
```json
{
  "status": "SUCCESS",
  "data": {
    "userId": 1,
    "facePaymentStatus": "ACTIVE",
    "message": "Face payment activated successfully"
  }
}
```

---

## Step 7 — Add Products to Store

> Requires token.

```bash
# Coffee
curl -X POST http://localhost:8080/api/store/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"name":"Coffee","description":"Arabica black coffee","price":25000,"stock":50}'

# Sandwich
curl -X POST http://localhost:8080/api/store/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"name":"Sandwich","description":"Chicken sandwich","price":35000,"stock":30}'

# Mineral Water
curl -X POST http://localhost:8080/api/store/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{"name":"Mineral Water","description":"500ml mineral water","price":10000,"stock":100}'
```

Check all products:
```bash
curl http://localhost:8080/api/store/products \
  -H "Authorization: Bearer <your_token>"
```

---

## Step 8 — Checkout with Face Payment

> Requires token.

```bash
curl -X POST http://localhost:8080/api/store/orders/checkout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "userId": 1,
    "items": [
      { "productId": 1, "quantity": 2 },
      { "productId": 3, "quantity": 1 }
    ]
  }'
```

**What happens:**
1. Spring Boot validates the JWT token
2. Validates balance and face payment status
3. Camera window **"Face Verification"** opens
4. Look at the camera
5. DeepFace checks liveness (anti-spoof) — orange box while checking
6. Once confirmed live → KNN matches your face — green box
7. **"VERIFIED!"** shown on screen for 1 second → window closes
8. Balance is deducted and order is saved

Expected response (success):
```json
{
  "status": "SUCCESS",
  "data": {
    "orderId": 1,
    "status": "SUCCESS",
    "items": [
      { "productName": "Coffee",        "quantity": 2, "subtotal": 50000 },
      { "productName": "Mineral Water", "quantity": 1, "subtotal": 10000 }
    ],
    "totalAmount": 60000,
    "remainingBalance": 4940000
  }
}
```

---

## All API Endpoints

### Public (no token required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register` | Register bank user |
| POST | `/api/auth/login` | Login and get JWT token |

### Protected (token required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/{id}` | Get user profile |
| POST | `/api/face/activate/{userId}` | Activate face payment |
| GET | `/api/face/status/{userId}` | Check face payment status |
| POST | `/api/payment/pay` | Direct bank payment with face |
| GET | `/api/store/products` | List all products |
| GET | `/api/store/products/{id}` | Get product detail |
| POST | `/api/store/products` | Add new product |
| POST | `/api/store/orders/checkout` | Checkout with face payment |
| GET | `/api/store/orders/{userId}` | View order history |

---

## Error Responses

| Status | Meaning |
|--------|---------|
| `INVALID_CREDENTIALS` | Wrong email or password on login |
| `EMAIL_EXISTS` | Email already registered |
| `USER_NOT_FOUND` | User ID does not exist |
| `FACE_ALREADY_ACTIVE` | Face payment already enrolled |
| `FACE_NOT_ACTIVE` | Face payment not yet activated |
| `FACE_MISMATCH` | Face did not match — transaction rejected |
| `INSUFFICIENT_BALANCE` | Not enough balance |
| `OUT_OF_STOCK` | Product stock is insufficient |
| `PRODUCT_NOT_FOUND` | Product ID does not exist |
| `VALIDATION_ERROR` | Missing or invalid request fields |

Example:
```json
{
  "status": "FACE_MISMATCH",
  "message": "Face verification failed. Order rejected.",
  "data": null
}
```

Calling a protected endpoint without a token returns an empty `403` response.

---

## Stop All Services

```bash
# Stop face service and Spring Boot
pkill -f face_service.py
pkill -f spring-boot

# Stop PostgreSQL
docker stop facepayment-postgres
```

---

## Database Credentials

| Field | Value |
|-------|-------|
| Host | localhost:5432 |
| Database | facepaymentdb |
| Username | facepayment |
| Password | facepayment123 |

Connect via psql:
```bash
docker exec -it facepayment-postgres psql -U facepayment -d facepaymentdb
```

---

## Tips

- **Camera not opening?** Make sure no other app is using the camera.
- **Always FAKE / red box?** Improve lighting — DeepFace anti-spoof needs a clear, well-lit face.
- **Enrollment too slow?** Reduce `ENROLL_SAMPLES` in `face_service.py` line 10 from `100` to `50`.
- **KNN never matches?** Re-enroll your face in the same lighting conditions as when verifying.
- **Token expired?** Tokens last 24 hours — just call `/api/auth/login` again to get a new one.
