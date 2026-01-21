# Backend

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── models/          # SQLAlchemy models (database entities)
├── schemas/         # Pydantic schemas (API contracts)
├── repositories/    # Data access layer
├── services/        # Business logic
├── api/            # API routes
└── core/           # Core utilities (database, logging, exceptions)
```

## Testing

```bash
pytest
```
