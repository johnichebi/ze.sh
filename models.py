from pydantic import BaseModel

class RegisterUser(BaseModel):
    username: str
    display_name: str
    password: str

class LoginUser(BaseModel):
    username: str
    password: str

class UpdateProfile(BaseModel):
    display_name:str
    bio:str
    pfp_url: str = None

class CreatePost(BaseModel):
    content: str
    media_url: str = None

class UpdatePost(BaseModel):
    content:str

class LikePost(BaseModel):
    post_id: str

class Follows(BaseModel):
    following_user_id: str

class CreateComment(BaseModel):
    post_id: str
    content: str

class LikeComment(BaseModel):
    comment_id: str
    user_id: str
