from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.models.user import User, PersonalPreferences
from backend.app.models.twin import PersonalTwinState
from backend.app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    PreferencesUpdateRequest,
    PreferencesResponse,
    TwinStateResponse,
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/api/users", tags=["Users & Preferences"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == request.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Create user
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        name=request.name.strip(),
    )
    db.add(user)
    await db.flush()  # populate user.id

    # Initialize default PersonalPreferences
    prefs = PersonalPreferences(user_id=user.id)
    db.add(prefs)

    # Initialize default PersonalTwinState
    twin = PersonalTwinState(
        user_id=user.id,
        timestamp=datetime.utcnow(),
        lighting_weight=0.20,
        crime_weight=0.25,
        isolation_weight=0.20,
        crowd_weight=0.15,
        traffic_weight=0.10,
        distance_weight=0.10,
        time_weight=0.15,
        night_weight=0.20,
        weather_weight=0.05,
        detour_tolerance=0.25,
        model_confidence=0.10,
    )
    db.add(twin)

    await db.commit()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == request.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# -------------------------------------------------------------
# USER PREFERENCES & TWIN STATE ENDPOINTS
# -------------------------------------------------------------

@user_router.get("/me/preferences", response_model=PreferencesResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PersonalPreferences).where(PersonalPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = PersonalPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs


@user_router.put("/me/preferences", response_model=PreferencesResponse)
async def update_my_preferences(
    request: PreferencesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PersonalPreferences).where(PersonalPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = PersonalPreferences(user_id=current_user.id)
        db.add(prefs)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)

    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs


@user_router.get("/me/twin", response_model=TwinStateResponse)
async def get_my_twin_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PersonalTwinState).where(PersonalTwinState.user_id == current_user.id)
    )
    twin = result.scalar_one_or_none()
    if not twin:
        twin = PersonalTwinState(
            user_id=current_user.id,
            timestamp=datetime.utcnow(),
        )
        db.add(twin)
        await db.commit()
        await db.refresh(twin)
    return twin

