from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File
from auth import get_current_user
from routers import posts, social, users
from fastapi.staticfiles import StaticFiles

app=FastAPI(title="ze.sh")

app.include_router(posts.router)
app.include_router(social.router)
app.include_router(users.router)

app.add_middleware(
            CORSMiddleware,
                allow_origins=["*"],
                    allow_credentials=True,
                        allow_methods=["*"],
                            allow_headers=["*"],
                            )

@app.get("/welcome")
async def welcome(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

app.mount("/", StaticFiles(directory="frontend",html=True), name="frontend")


