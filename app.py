from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_routes.routers import router


app = FastAPI(title="TestApi", version="0.2.0")


app.include_router(router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, lifespan="on")
