from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI()

# Enable CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Interactive Health Dashboard API"}

@app.get("/ping")
def ping():
    return {"message": "API is running"}
# from fastapi import FastAPI
# from routes import router

# app = FastAPI()

# app.include_router(router)

# @app.get("/ping")
# def ping():
#     return {"message": "API is running"}
