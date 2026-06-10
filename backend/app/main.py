from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_game import repository as daily_repository
from app.api.routes_game import router as daily_router
from app.api.routes_rooms import repository as room_repository
from app.api.routes_rooms import router as rooms_router


app = FastAPI(title="Newmantle Clone API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(daily_router)
app.include_router(rooms_router)


@app.on_event("startup")
def initialize_storage() -> None:
    daily_repository.init_db()
    room_repository.init_db()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
