from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user


router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me")
async def get_user_profile(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "name": current_user.full_name or current_user.username,
        "username": current_user.username,
        "email": current_user.email,
        "groups": current_user.groups,
        "avatar_url": "",
    }
