from fastapi import APIRouter

from app.models.data_room import DataRoomResponse
from app.services.data_room.demo_data_room import get_demo_data_room_readiness

router = APIRouter()


@router.get("/demo-readiness", response_model=DataRoomResponse)
async def get_demo_readiness_endpoint():
    return get_demo_data_room_readiness()
