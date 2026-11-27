from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user, hash_password, verify_hash_password, create_access_token, verify_access_token
from database import execute_query
from models import RegisterUser, LoginUser, UpdateProfile
from uuid import uuid4
from datetime import timedelta
import cloudinary_config
import cloudinary.uploader

router = APIRouter(prefix = "/account")

@router.get("/me")
async def me(current_user = Depends(get_current_user)):
    return {
            k:current_user[k] for k in ("user_id", "user_name", "display_name", "bio", "pfp_url")
            }

@router.get("/profile/{username}/posts")
def user_posts(username: str):
    query = """SELECT
    posts.post_id, posts.user_id, users.user_name, posts.content, posts.created_at,
    (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id) AS like_count,
    COALESCE((SELECT json_agg(media_url) FROM post_media
              WHERE post_media.post_id = posts.post_id), '[]'::json) AS media_urls
    FROM posts
    JOIN users ON users.user_id = posts.user_id
    WHERE users.user_name = :username
    ORDER BY posts.created_at DESC
    LIMIT 50
    """
    return execute_query(query, {"username": username}).mappings().all()

@router.get("/search")
def search_users(q: str = ""):
    q = q.strip().lstrip("@")
    if not q:
        return []
    safe = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    query = """SELECT user_name, display_name, pfp_url
    FROM users
    WHERE user_name ILIKE :contains OR display_name ILIKE :contains
    ORDER BY (user_name ILIKE :prefix) DESC, user_name
    LIMIT 20
    """
    return execute_query(query, {"contains": "%" + safe + "%", "prefix": safe + "%"}).mappings().all()

@router.post("/register")
async def register(
    user_name=Form(...),
    display_name=Form(...),
    password=Form(...)):
    user_id=str(uuid4())
    query="""
        INSERT INTO users (user_id, user_name, display_name, password_hash)
        VALUES(:user_id, :user_name, :display_name, :password_hash)
            """
    bind_params= {
            "user_id":user_id,
            "user_name":user_name,
            "display_name":display_name,
            "password_hash":hash_password(password)
            }
    result = execute_query(query, bind_params)

    return {
            "user_id":user_id,
            "username":user_name,
            "followers": -1,
            "following":-1
            }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm= Depends()):
    query="""
    SELECT password_hash FROM users WHERE user_name=:user_name
    """
    result = execute_query(query, {"user_name": form_data.username,}).mappings().first()
    if result:
        if verify_hash_password(form_data.password, result["password_hash"]):
            token = create_access_token({"sub": form_data.username}, expires_delta=timedelta(minutes=29))
            return {"access_token": token, "token_type":"bearer"}
    return False

@router.patch("/profile")
async def edit_profile(display_name:str|None=Form(None), bio:str|None=Form(None), current_user = Depends(get_current_user), file: UploadFile | None = File(None)):
    pfp_url = None
    if file:
        pfp_url = cloudinary.uploader.upload(file.file)["secure_url"]
    query = """
   UPDATE users
   SET
       display_name = COALESCE(:display_name, display_name),
           bio = COALESCE(:bio, bio),
               pfp_url = COALESCE(:pfp_url, pfp_url)
               WHERE user_name = :username
               RETURNING *
               """
    result=execute_query(query, {"username":current_user["user_name"], "display_name":display_name, "bio":bio, "pfp_url":pfp_url})
    updated = result.mappings().first()
    if updated:
        return dict(updated)
    raise HTTPException(status_code=403, detail="User not found")

@router.delete("/profile")
async def delete_profile(current_user = Depends(get_current_user)):
        query = "DELETE FROM users WHERE user_name = :username"
        result=execute_query(query,{"username":current_user["user_name"]})
        if result.rowcount > -1:
            return {"detail":"Account successfully deleted!"}
        raise HTTPException(status_code=403, detail="User not found")

@router.get("/profile/{username}")
async def get_profile(username):
    query = """SELECT
    user_id,
    user_name,
    display_name,
    bio,
    pfp_url,
    (SELECT COUNT(*) FROM follows WHERE following_user_id=users.user_id) AS followers,
    (SELECT COUNT(*) FROM follows WHERE follower_user_id=users.user_id) AS following
    FROM users 
    WHERE user_name= :username
    """
    result=execute_query(query, {"username":username}).mappings().first()

    if not result:
        raise HTTPException(status_code=403, detail="User not found")
    return dict(result)
