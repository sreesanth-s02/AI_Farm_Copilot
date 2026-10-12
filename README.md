# AI Farm Copilot 🌱

AI Farm Copilot is a precision-agriculture decision-support project designed to help farmers understand field conditions, access weather information, and make more informed irrigation decisions.

The project currently provides a Python FastAPI backend, MySQL database integration, weather data from Open-Meteo, Redis-compatible caching, and rule-based irrigation assessments.

> **Project status:** Backend APIs and automated tests are implemented. Irrigation thresholds are prototype rules and have not been agronomically validated. Additional ML capabilities are planned.

## Features

- **Farmer management:** Create and retrieve farmer records.
- **Farm management:** Store farm information and associate farms with farmers.
- **Field management:** Manage field areas, soil types, and geographical coordinates.
- **Crop management:** Record crop varieties, dates, growth stages, and status.
- **Soil readings:** Store soil nutrients, pH, moisture, and organic carbon.
- **Weather information:** Retrieve current conditions and hourly forecasts from Open-Meteo.
- **Weather caching:** Cache weather responses using Redis or Memurai.
- **Irrigation assessment:** Evaluate soil moisture and forecast rainfall using prototype decision rules.
- **Automated tests:** Test API validation, error handling, caching, and irrigation logic.

## Technology Stack

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI |
| API server | Uvicorn |
| Database | MySQL |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| Cache | Redis / Memurai |
| Weather data | Open-Meteo |
| Validation | Pydantic |
| Testing | Pytest |

## Project Structure

```text
AI_Farm_Copilot/
├── README.md
└── backend/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── db/
    │   ├── models/
    │   ├── schemas/
    │   ├── services/
    │   └── main.py
    ├── alembic/
    │   └── versions/
    ├── tests/
    ├── .env.example
    ├── .gitignore
    ├── alembic.ini
    └── requirements.txt
```

## Prerequisites

Install or configure the following before running the backend:

- Python 3.11 or newer, compatible with the project dependencies.
- MySQL 8.x or another compatible MySQL server.
- Redis or Memurai for weather caching.
- Git.
- An internet connection for live weather requests to Open-Meteo.

## Installation on Windows

### 1. Clone the repository

```cmd
git clone https://github.com/sreesanth-s02/AI_Farm_Copilot.git
cd AI_Farm_Copilot
cd backend
```

### 2. Create and activate a virtual environment

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local environment file from the example:

```cmd
copy .env.example .env
notepad .env
```

Replace `YOUR_MYSQL_USER` and `YOUR_MYSQL_PASSWORD` with your own MySQL credentials.

Example format:

```env
DATABASE_URL=mysql+pymysql://YOUR_MYSQL_USER:YOUR_MYSQL_PASSWORD@localhost:3306/ai_farm_copilot
REDIS_URL=redis://localhost:6379/0
```

Use your own credentials. If the database password contains special URL characters, URL-encode them in the connection string.

Do not commit `.env` to GitHub.

### 5. Create the MySQL database

Start MySQL and open a MySQL client:

```cmd
mysql -u YOUR_MYSQL_USER -p
```

Enter your password when prompted. Then execute:

```sql
CREATE DATABASE ai_farm_copilot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Exit the MySQL client:

```sql
EXIT;
```

If the database already exists, you do not need to create it again.

### 6. Apply database migrations

Ensure you are inside the `backend` directory with the virtual environment activated.

Run:

```cmd
alembic upgrade head
```

This applies the project's Alembic migrations to the configured database.

### 7. Start the backend

```cmd
uvicorn app.main:app --reload
```

The API should be available at:

- API base: http://127.0.0.1:8000
- Interactive Swagger documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Database health check: http://127.0.0.1:8000/health/database

Keep the terminal running while using the API.

## API Endpoints

All API routes use the `/api/v1` prefix unless stated otherwise.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/farmers` | Create a farmer |
| GET | `/api/v1/farmers/{farmer_id}` | Retrieve a farmer |
| POST | `/api/v1/farms` | Create a farm |
| GET | `/api/v1/farms/{farm_id}` | Retrieve a farm |
| GET | `/api/v1/farms/farmer/{farmer_id}` | List a farmer's farms |
| POST | `/api/v1/fields` | Create a field |
| GET | `/api/v1/fields/{field_id}` | Retrieve a field |
| GET | `/api/v1/fields/farm/{farm_id}` | List a farm's fields |
| POST | `/api/v1/crops` | Create a crop record |
| GET | `/api/v1/crops/{crop_id}` | Retrieve a crop |
| GET | `/api/v1/crops/field/{field_id}` | List crops for a field |
| POST | `/api/v1/soil` | Create a soil reading |
| GET | `/api/v1/soil/{reading_id}` | Retrieve a soil reading |
| GET | `/api/v1/soil/field/{field_id}` | List soil readings for a field |
| GET | `/api/v1/weather/current` | Get current weather |
| GET | `/api/v1/weather/hourly` | Get hourly weather forecasts |
| GET | `/api/v1/recommendations/irrigation/{field_id}` | Assess irrigation conditions |

Weather endpoints require `latitude` and `longitude` query parameters.

Example:

```text
http://127.0.0.1:8000/api/v1/weather/current?latitude=12.9716&longitude=80.244
```

For the complete request and response schemas, visit `/docs`.

## Running Tests

From the `backend` directory, with the virtual environment activated:

```cmd
python -m pytest -v
```

The current project test suite contains 60 tests covering irrigation rules, API endpoints, weather service caching, validation, and error handling.

## Important Notes

- MySQL must be running and the `.env` database URL must be valid.
- Redis or Memurai should be running for weather caching. Cache failures are handled by the weather service, but a working cache is recommended.
- Live weather requests require internet access.
- Irrigation decisions currently use prototype thresholds, not an agronomically validated model. Do not treat them as definitive agricultural advice.
- Machine-learning recommendations and the Flutter client are planned extensions, not features claimed to be complete in this backend version.
- Never commit passwords, API keys, or personal credentials.

## Future Enhancements

- Train and evaluate crop recommendation models.
- Integrate validated soil and crop datasets.
- Expand decision-support recommendations.
- Build a Flutter mobile interface.
- Add Tamil-language support and farmer-friendly explanations.

## License

A license has not yet been specified. Add an appropriate license before redistributing the project if needed.
