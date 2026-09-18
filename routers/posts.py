from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from auth import get_current_user
from database import execute_query
from models import CreatePost, UpdatePost
from uuid import uuid4
from typing import Annotated
import cloudinary.uploader
import cloudinary_config

router=APIRouter()

@router.post("/posts")
async def create_post(current_user=Depends(get_current_user), files: Annotated[list[UploadFile]|None, File()]=[], content:Annotated[str|None, Form()]=None):
    files = files or []
    if not files and not content:
        raise HTTPException(400, detail="Post must contain text or media")
    media_url = None
    if len(files) > 4:
        raise HTTPException(400, detail="4 maximum uploads allowed.")
    post_id = str(uuid4())
    user_id = execute_query("select * from users where user_name = :user_name", {"user_name":current_user["user_name"]}).mappings().first()
    if user_id:
        user_id = dict(user_id)["user_id"]
    else:
        raise HTTPException(status_code=404, detail="User not found")
    query = "INSERT INTO posts (user_id, post_id, content) values (:user_id, :post_id, :content) RETURNING *"
    bind_params = {
        "user_id":user_id,
        "post_id":post_id,
        "content":content
            }
    result = execute_query(query, bind_params).mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Error creating post.")

    urls=[]
    for file in files:
        media_url = cloudinary.uploader.upload(file.file, resource_type="auto")["secure_url"]
        urls.append(media_url)
        media_query = execute_query("""
                            INSERT INTO post_media (media_url, post_id) 
                            VALUES (:media_url, :post_id) 
                            RETURNING *""",                                                                {
                    "media_url":media_url,
                    "post_id":post_id}).mappings().first()

        if not media_query:
            raise HTTPException(500, detail="Unable to upload media.")
    result["media_urls"]=urls
    return dict(result)

@router.get("/posts/feed")
def fetch_feed():
    query="""SELECT 
    posts.user_id, 
    posts.post_id,
    users.user_name,
    posts.content,
    posts.created_at,
    COUNT(likes.user_id) AS like_count 
    FROM posts
    JOIN users ON users.user_id = posts.user_id
    LEFT JOIN likes ON likes.post_id = posts.post_id
    GROUP BY posts.post_id, posts.user_id, users.user_name, posts.content
    ORDER BY created_at DESC
    LIMIT 20
    """
    result = execute_query(query).mappings().all()

    if result:
        return result
    raise HTTPException(status_code=403,detail="Error loading Feed")

@router.get("/posts/{post_id}")
def get_post(post_id):
    query="""SELECT 
    posts.post_id, 
    user_name, 
    content, 
    posts.user_id, 
    COUNT(likes.user_id) as like_count 
    FROM posts 
    JOIN users ON posts.user_id = users.user_id 
    LEFT JOIN likes ON posts.post_id = likes.post_id 
    WHERE posts.post_id = :post_id
    GROUP BY posts.post_id, users.user_id, posts.content, posts.user_id
    """
    result = execute_query(query, {"post_id": post_id}).mappings().first()
    if result:
        return dict(result)
    raise HTTPException(status_code=404, detail="Post not found.")

@router.delete("/posts/{post_id}")
def delete_post(post_id:str, current_user = Depends(get_current_user)):
    query="DELETE FROM posts WHERE post_id = :post_id AND user_id=(SELECT user_id FROM users WHERE user_name=:user_name)"
    result=execute_query(query, {"post_id":post_id, "user_name":current_user["user_name"]})
    if result.rowcount>0:
        return {"message": "Post deleted successfully."}
    raise HTTPException(status_code=403, detail="Forbidden")

@router.patch("/posts/{post_id}")
def update_post(post: UpdatePost, post_id: str, current_user= Depends(get_current_user)):
    query="UPDATE posts SET content = :content WHERE post_id = :post_id AND user_id=(SELECT user_id FROM users WHERE user_name=:user_name)"
    bind_params = {"content": post.content, "post_id":post_id, "user_name":current_user["user_name"]}
    result = execute_query(query, bind_params)
    if result.rowcount>0:
        return {
                "post_id":post_id,
                "content": post.content
                }
    raise HTTPException(
            status_code=403,
            detail="Forbidden"
            
)
