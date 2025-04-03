import secrets

from fastapi import FastAPI

from app.routes import private_router, public_router

app = FastAPI()

app.include_router(public_router)
app.include_router(private_router)

# token = secrets.token_hex(32)
# print(token)