# Python CRUD Aquatic

FastAPI service for querying ocean species, habitats, observers, sightings, and
summary statistics.

## Run the API

Set `DATABASE_URL` (or add it to `.env`), then start the app from the project
root:

```powershell
uvicorn main:app --reload
```

The application is defined in `src/pythoncrudaquatic/app.py`. `main.py` remains
as a compatibility entry point. Each layer has its own package folder:

- `src/pythoncrudaquatic/routes/` — FastAPI paths, query parameters, and response models
- `src/pythoncrudaquatic/controllers/` — HTTP status handling and request-to-service coordination
- `src/pythoncrudaquatic/services/` — application workflows and existence checks
- `src/pythoncrudaquatic/repositories/` — SQL queries and database access
- `src/pythoncrudaquatic/db.py` and `src/pythoncrudaquatic/schemas.py` — database setup and response schemas