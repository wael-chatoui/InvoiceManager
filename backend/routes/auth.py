from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from services.supabase_client import get_supabase, get_supabase_admin

router = APIRouter(prefix="/auth", tags=["auth"])


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


def get_current_user(authorization: str = Header(...)):
    """Extract and verify the current user from the Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return {"user": user_response.user, "token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.post("/signup")
async def sign_up(request: SignUpRequest):
    """Register a new user."""
    try:
        supabase = get_supabase()

        # Sign up the user
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name or ""
                }
            }
        })

        if auth_response.user is None:
            raise HTTPException(status_code=400, detail="Failed to create user")

        return {
            "message": "User created successfully. Please check your email for verification.",
            "user": {
                "id": str(auth_response.user.id),
                "email": auth_response.user.email
            }
        }
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg:
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=400, detail=f"Signup failed: {error_msg}")


@router.post("/signin")
async def sign_in(request: SignInRequest):
    """Sign in an existing user."""
    try:
        supabase = get_supabase()

        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if auth_response.session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": str(auth_response.user.id),
                "email": auth_response.user.email,
                "full_name": auth_response.user.user_metadata.get("full_name", "")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Sign in failed: {str(e)}")


@router.post("/signout")
async def sign_out(current_user: dict = Depends(get_current_user)):
    """Sign out the current user."""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
        return {"message": "Successfully signed out"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sign out failed: {str(e)}")


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh the access token."""
    try:
        supabase = get_supabase()

        auth_response = supabase.auth.refresh_session(refresh_token)

        if auth_response.session is None:
            raise HTTPException(status_code=401, detail="Failed to refresh token")

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get the current user's information."""
    user = current_user["user"]

    try:
        # Get profile from database
        supabase = get_supabase()
        profile_response = supabase.table("profiles").select("*").eq("id", str(user.id)).single().execute()

        profile = profile_response.data if profile_response.data else {}

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": profile.get("full_name", user.user_metadata.get("full_name", "")),
            "company_name": profile.get("company_name", ""),
            "address": profile.get("address", ""),
            "phone": profile.get("phone", "")
        }
    except Exception as e:
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.user_metadata.get("full_name", ""),
            "company_name": "",
            "address": "",
            "phone": ""
        }


@router.put("/profile")
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update the current user's profile."""
    user = current_user["user"]

    try:
        supabase = get_supabase()

        # Build update data (only include non-None fields)
        update_data = {}
        if profile_update.full_name is not None:
            update_data["full_name"] = profile_update.full_name
        if profile_update.company_name is not None:
            update_data["company_name"] = profile_update.company_name
        if profile_update.address is not None:
            update_data["address"] = profile_update.address
        if profile_update.phone is not None:
            update_data["phone"] = profile_update.phone

        if update_data:
            result = supabase.table("profiles").update(update_data).eq("id", str(user.id)).execute()

        return {"message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Profile update failed: {str(e)}")
