from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, users, subscriptions, jobs, cv

app = FastAPI(
    title="JobBot API", version="1.0.0", description="API para el servicio JobBot SaaS"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tu-dominio.com",
        "https://jobbot.ar",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(
    subscriptions.router, prefix="/subscriptions", tags=["subscriptions"]
)
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(cv.router, prefix="/cv", tags=["cv"])


@app.get("/")
def root():
    return {"message": "JobBot API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
