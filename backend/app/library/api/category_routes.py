from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.library.api.schemas import CategorySchema
from app.library.repositories import CategoryRepository
from app.users.api.user_routes import get_current_user_dependency

router = APIRouter(prefix="/api/v1/library/categories", tags=["library", "categories"])


@router.get("/", response_model=list[CategorySchema])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
) -> list[CategorySchema]:
    """List all categories."""
    category_repo = CategoryRepository(db)
    categories = await category_repo.list_all()
    return [CategorySchema.model_validate(c) for c in categories]
