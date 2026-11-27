from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import execute_query
from models import Follows, LikeComment, LikePost, CreateComment
from uuid import uuid4

router = APIRouter()

@router.post("/follow")
def follow_user(user:Follows, current_user=Depends(get_current_user)):
    query="INSERT INTO follows (follower_user_id, following_user_id) VALUES ((SELECT user_id from users WHERE user_name=:username), :following_user_id) ON CONFLICT (follower_user_id, following_user_id) DO NOTHING RETURNING *"
    result = execute_query(query, {"username": current_user["user_name"], "following_user_id":user.following_user_id}).mappings().first()
    if result:
        return {"message":"Followed"}
    deleted = execute_query("DELETE FROM follows WHERE follower_user_id= (SELECT user_id FROM users WHERE user_name=:username) AND following_user_id = :following_user_id", {"username": current_user["user_name"], "following_user_id":user.following_user_id})
    if deleted.rowcount>0:
        return {"message":"Unfollowed"}
    raise HTTPException(status_code=404, detail="Couldn't follow user")

@router.post("/like_post")
def like_post(post:LikePost, current_user=Depends(get_current_user)):
    query="INSERT INTO likes (user_id, post_id) VALUES ((SELECT user_id FROM users WHERE user_name = :user_name), :post_id) ON CONFLICT (user_id, post_id) DO NOTHING RETURNING *"
    result = execute_query(query, {"user_name":current_user["user_name"], "post_id":post.post_id}).mappings().first()
    if result:
        return {"message": "Post liked"}
    deleted = execute_query("DELETE FROM likes WHERE user_id = (SELECT user_id FROM users WHERE user_name=:user_name) AND post_id = :post_id", {"user_name":current_user["user_name"], "post_id":post.post_id})
    if deleted.rowcount>0:
        return {"message": "Post unliked"}
    raise HTTPException(status_code=404, detail="Post not found")

@router.post("/posts/comments")
def make_comment(comment:CreateComment, current_user=Depends(get_current_user)):
    query=""" INSERT INTO comments (
                user_id,
                comment_id,
                post_id,
                content)
                VALUES (
                    (SELECT user_id FROM users WHERE user_name=:user_name),
                    :comment_id,
                    :post_id,
                    :content)
                RETURNING *
            """
    result = execute_query(
            query,
            {
                "user_name": current_user["user_name"],
                "comment_id": str(uuid4()),
                "post_id": comment.post_id,
                "content":comment.content
                }
            ).mappings().first()
    if result:
        return result
    raise HTTPException(status_code=400, detail="Couldn't make comment")

@router.post("/like_comment")
def like_comment(comment:LikeComment, current_user=Depends(get_current_user)):
    query="INSERT INTO comment_likes (user_id, comment_id) VALUES ((SELECT user_id FROM users WHERE user_id=:user_id), :comment_id) ON CONFLICT (user_id, comment_id) DO NOTHING RETURNING *"
    result = execute_query(query, {"user_id":current_user["user_id"], "comment_id":comment.comment_id}).mappings().first()
    if result:
        return {"message": "Comment liked"}
    deleted = execute_query("DELETE FROM comment_likes WHERE user_id = :user_id AND comment_id = :comment_id", {"user_id":comment.user_id, "comment_id":comment.comment_id})
    if deleted.rowcount>0:
        return {"message": "Comment unliked"}
    raise HTTPException(status_code=404, detail="Comment not found")

@router.get("/comments/{comment_id}")
def get_comment(comment_id):
    query="""SELECT 
            comments.comment_id, 
            user_name, 
            users.pfp_url,
            content, 
            comments.user_id, 
            COUNT(comment_likes.user_id) as like_count 
            FROM comments 
            JOIN users ON comments.user_id = users.user_id 
            LEFT JOIN comment_likes ON comments.comment_id = comment_likes.comment_id 
            WHERE comments.comment_id = :comment_id
            GROUP BY comments.comment_id, users.user_id, users.pfp_url, comments.content, comments.user_id
            """
    result = execute_query(query, {"comment_id": comment_id}).mappings().first()
    if result:
        return dict(result)
     
    raise HTTPException(status_code=404, detail="Comment not found.")

@router.delete("/comments/{comment_id}")
def delete_comment(comment_id:str, current_user= Depends(get_current_user)):
    query="DELETE FROM comments WHERE comment_id = :comment_id AND user_id = (SELECT user_id FROM users WHERE user_id =:user_id)"
    result=execute_query(query, {"comment_id":comment_id, "user_id":current_user["user_id"]})
    if result.rowcount>0:
        return {"message": "Post deleted successfully."}
    raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/posts/{post_id}/comments")
def get_post_comments(post_id: str):
        query = """SELECT
                comments.comment_id,
                comments.user_id,
                users.user_name,
                comments.content,
                comments.created_at,
                COUNT(comment_likes.user_id) AS like_count
                FROM comments
                JOIN users ON users.user_id = comments.user_id
                LEFT JOIN comment_likes ON comment_likes.comment_id = comments.comment_id
                WHERE comments.post_id = :post_id
                GROUP BY comments.comment_id, comments.user_id, users.user_name,
                comments.content, comments.created_at
                ORDER BY comments.created_at ASC
                    """
        return execute_query(query, {"post_id": post_id}).mappings().all()


@router.get("/likes/me")
def my_likes(current_user=Depends(get_current_user)):
    rows = execute_query(
        "SELECT post_id FROM likes WHERE user_id = :user_id",
        {"user_id": current_user["user_id"]}
        ).mappings().all()

@router.get("/follows/me")
def my_follows(current_user=Depends(get_current_user)):
    rows = execute_query(
        "SELECT following_user_id FROM follows WHERE follower_user_id = :user_id",
        {"user_id": current_user["user_id"]}
    ).mappings().all()
    return [r["following_user_id"] for r in rows]
