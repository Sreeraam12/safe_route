from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.models.user import User, PersonalPreferences
from backend.app.models.twin import PersonalTwinState
from backend.app.models.trusted_contact import TrustedContact
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

    # Optional Trusted Contacts during registration
    if getattr(request, "trusted_contact_name", None) and getattr(request, "trusted_contact_phone", None):
        db.add(
            TrustedContact(
                owner_user_id=user.id,
                name=request.trusted_contact_name.strip(),
                phone_number=request.trusted_contact_phone.strip(),
                relationship=(getattr(request, "trusted_contact_relationship", None) or "Family").strip(),
                is_verified=True,
                is_active=True,
            )
        )
    if getattr(request, "trusted_contacts", None):
        for tc in request.trusted_contacts:
            if isinstance(tc, dict) and (tc.get("name") or tc.get("contact_name")) and tc.get("phone_number"):
                db.add(
                    TrustedContact(
                        owner_user_id=user.id,
                        name=str(tc.get("contact_name") or tc.get("name")).strip(),
                        phone_number=str(tc.get("phone_number")).strip(),
                        relationship=str(tc.get("relationship") or "Family").strip(),
                        is_verified=True,
                        is_active=True,
                    )
                )

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


@user_router.get("/me/segment-memory")
async def get_my_segment_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns personal segment memory statistics and active remembered corridors.
    """
    from backend.app.models.twin import PersonalSegmentMemory
    res = await db.execute(
        select(PersonalSegmentMemory).where(PersonalSegmentMemory.user_id == current_user.id)
    )
    memories = res.scalars().all()

    familiar = [m for m in memories if m.visit_count >= 2 or m.trust_score >= 0.65]
    avoided = [m for m in memories if m.avoidance_score >= 0.35 or m.rejection_count >= 3]

    sorted_trusted = sorted(memories, key=lambda m: (-m.trust_score, -m.visit_count))[:10]
    sorted_avoided = sorted(memories, key=lambda m: (-m.avoidance_score, -m.rejection_count))[:10]

    return {
        "user_id": current_user.id,
        "total_remembered_corridors": len(memories),
        "familiar_corridors_count": len(familiar),
        "avoided_corridors_count": len(avoided),
        "top_trusted_corridors": [
            {
                "osm_segment_id": m.osm_segment_id,
                "visit_count": m.visit_count,
                "selection_count": m.selection_count,
                "trust_score": m.trust_score,
                "personal_risk_adjustment": m.personal_risk_adjustment,
                "last_visit": m.last_visit.isoformat() if m.last_visit else None,
            }
            for m in sorted_trusted if m.trust_score > 0.5 or m.visit_count > 0
        ],
        "top_avoided_corridors": [
            {
                "osm_segment_id": m.osm_segment_id,
                "rejection_count": m.rejection_count,
                "negative_feedback_count": m.negative_feedback_count,
                "avoidance_score": m.avoidance_score,
                "personal_risk_adjustment": m.personal_risk_adjustment,
            }
            for m in sorted_avoided if m.avoidance_score > 0.1 or m.rejection_count > 0
        ],
    }

