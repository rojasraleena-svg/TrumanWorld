from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="健康检查",
    description="检查 API 服务是否正常运行",
    tags=["health"],
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
