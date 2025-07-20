from fastapi import APIRouter
from app.api.routers import auth, tasks, users, categories, tags, comments, files, search, analytics, webhooks, calendar, notifications
from app.api.endpoints import projects

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

# Include projects router
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# Include comments router  
api_router.include_router(comments.router, tags=["comments"])

# Include files router
api_router.include_router(files.router, tags=["files"])

# Include search router
api_router.include_router(search.router, tags=["search"])

# Include analytics router
api_router.include_router(analytics.router, tags=["analytics"])

# Include webhooks router
api_router.include_router(webhooks.router, tags=["webhooks"])

# Include calendar router
api_router.include_router(calendar.router, tags=["calendar"])

# Include notifications router
api_router.include_router(notifications.router, tags=["notifications"])