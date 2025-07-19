from fastapi import APIRouter
from app.api.routers import auth, tasks, users, categories, tags

api_router = APIRouter()

# Include auth router (login, register)
api_router.include_router(auth.router, tags=["auth"])

# Include users router
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include tasks router
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# Include categories router
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])

# Include tags router
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])