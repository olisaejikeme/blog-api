from datetime import timedelta, datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.database import get_db
from app.models import User, Post, Comment
from app.schemas import UserCreate, UserLogin, PostCreate, CommentCreate, PostUpdate

public_router = APIRouter()
private_router = APIRouter(dependencies=[Depends(get_current_user)])

@public_router.post("/users/register", response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    user = User (
        username=user.username,
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}

@public_router.post("/users/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # Retrieve user from the database
    db_user = db.query(User).filter(User.username == user.username).first()

    # If user does not exist, raise an error
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify the password
    if not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": db_user.username})

    return {"access_token": access_token, "token_type": "bearer"}

@private_router.get("/protected")
async def protected_route():
    return "Protected route"

@private_router.post("/posts")
async def create_post(post: PostCreate,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="Unauthorized")

    post = Post (
        title=post.title,
        content=post.content,
        author_id=current_user.id
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return {"message": "Post created successfully"}

@private_router.get("/posts")
async def get_all_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()

@private_router.get("/posts/{post_id}")
async def get_post_by_id(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post

@private_router.post("/posts/{post_id}/comments")
async def create_comment(post_id: int,
                         comment: CommentCreate,
                         db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment (
        content=comment.content,
        post_id=post_id
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {"message": "Comment created successfully", "comment_id": comment.id}

@private_router.get("/posts/{post_id}/comments")
async def get_comments_by_post_id(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = db.query(Comment).filter(Comment.post_id == post_id).all()

    return comments

@private_router.put("/posts/{post_id}")
async def update_post(post_id: int,
                      updated_post: PostUpdate,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to modify this post")

    # Update only the provided fields
    if updated_post.title is not None:
        post.title = updated_post.title

    if updated_post.content is not None:
        post.content = updated_post.content

    # If nothing is updated, return an error
    if updated_post.title is None and updated_post.content is None:
        raise HTTPException(status_code=400, detail="No updates provided")

    db.commit()
    db.refresh(post)

    return {"message": "Post updated successfully", "post_id": post.id}

@private_router.delete("/posts/{post_id}")
async def delete_post(post_id: int,
                      db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this post")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully", "post_id": post.id}