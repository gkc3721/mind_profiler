from fastapi import APIRouter, HTTPException
from app.core.profiles_manager import (
    list_profile_sets,
    get_profile_set,
    save_profile_set,
    delete_profile_set
)
from app.models.profiles import ProfileSet, ProfileSetSummary

router = APIRouter()


@router.get("", response_model=list[ProfileSetSummary])
async def list_profiles_endpoint():
    """List all available profile sets"""
    return list_profile_sets()


@router.get("/{profile_set_id}", response_model=ProfileSet)
async def get_profile_set_endpoint(profile_set_id: str):
    """Get a specific profile set by ID"""
    try:
        return get_profile_set(profile_set_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=ProfileSet)
async def create_profile_set_endpoint(profile_set: ProfileSet):
    """Create a new profile set"""
    try:
        save_profile_set(profile_set)
        return profile_set
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{profile_set_id}", response_model=ProfileSet)
async def update_profile_set_endpoint(profile_set_id: str, profile_set: ProfileSet):
    """Update an existing profile set"""
    if profile_set.id != profile_set_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    try:
        save_profile_set(profile_set)
        return profile_set
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{profile_set_id}")
async def delete_profile_set_endpoint(profile_set_id: str):
    """Delete a profile set (cannot delete 'meditasyon')"""
    if profile_set_id == "meditasyon":
        raise HTTPException(status_code=400, detail="Cannot delete default profile set 'meditasyon'")
    try:
        delete_profile_set(profile_set_id)
        return {"status": "deleted", "id": profile_set_id}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))
