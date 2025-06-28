
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from modules import Apis
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request


app = FastAPI()

# # --------------allow cors--------------------------
# origins = [
#     "http://localhost:3000",
#     "localhost:3000",
# ]

# A "middleware" is a function that works with every request before it is processed by any specific path operation.
# And also with every response before returning it. refer docs for more info
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# -- APIs'
app.include_router(Apis.router)

app.mount('/', StaticFiles(directory="../static", html=True), name="static")



