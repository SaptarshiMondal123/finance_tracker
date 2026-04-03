from fastapi import FastAPI
from fastapi.responses import Response
from database import Base, engine
from routers import auth, transactions, summary, users

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Tracker API",
    description="""
## 💰 Finance Tracker API

A Python-powered backend for managing personal financial records with role-based access control.

### Roles
| Role     | Permissions                                      |
|----------|--------------------------------------------------|
| viewer   | View own transactions                            |
| analyst  | View & filter transactions, access summary, export |
| admin    | Full CRUD, manage users, all of the above        |

### Quick Start
1. **Register** a user via `POST /auth/register`
2. **Login** via `POST /auth/login` to get your JWT token
3. Click **Authorize** (top right) and paste: `Bearer <your_token>`
4. Start using the API!
    """,
    version="1.0.0",
)

# Include all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router)
app.include_router(summary.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Finance Tracker API is running",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
