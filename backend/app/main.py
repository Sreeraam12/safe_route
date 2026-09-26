from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db.session import init_db
from backend.app.api.routes import router as routes_router
from backend.app.api.auth import router as auth_router, user_router
from backend.app.api.trips import router as trips_router
from backend.app.api.navigation import router as navigation_router
from backend.app.api.sos_routes import emergency_router, sos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title='Safe Route API',
    version='0.1.0',
    description='Chennai Safe Route Prediction, Personal Digital Twin & Live Navigation API',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health_check():
    return {'status': 'ok', 'service': 'SafeRoute API'}


app.include_router(routes_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(trips_router)
app.include_router(navigation_router)
app.include_router(emergency_router)
app.include_router(sos_router)
