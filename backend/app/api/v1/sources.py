import asyncio

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.data_source import DataSource
from app.schemas.source import SourceCreateRequest, SourceResponse, SourcePreviewResponse
from app.api.deps import get_current_user
from app.services.scraper import detect_platform
from app.services.analysis import process_source

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    req: SourceCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url_str = str(req.url)
    platform = req.platform or detect_platform(url_str)

    source = DataSource(
        user_id=user.id,
        platform=platform,
        source_url=url_str,
        status="pending",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    # Trigger async scraping in background
    asyncio.create_task(process_source(source.id))
    return source


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataSource)
        .where(DataSource.user_id == user.id)
        .order_by(DataSource.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{source_id}/rescan", response_model=SourceResponse)
async def rescan_source(
    source_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.status = "pending"
    source.error_message = None
    await db.commit()
    await db.refresh(source)

    # Trigger async re-scraping in background
    asyncio.create_task(process_source(source.id))
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()


@router.get("/{source_id}/preview", response_model=SourcePreviewResponse)
async def preview_source(
    source_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    data_quality = None
    if source.parsed_data:
        data_quality = source.parsed_data.get("data_quality", "unknown")

    return SourcePreviewResponse(
        id=str(source.id),
        platform=source.platform,
        source_url=source.source_url,
        parsed_data=source.parsed_data,
        data_quality=data_quality,
    )


@router.patch("/{source_id}/confirm", response_model=SourceResponse)
async def confirm_source(
    source_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.user_id == user.id,
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.is_confirmed = True
    await db.commit()
    await db.refresh(source)
    return source


@router.post("/resume/upload", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 10MB")

    source = DataSource(
        user_id=user.id,
        platform="resume",
        source_url=f"upload://{file.filename}",
        status="pending",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    # TODO: Save file to S3, trigger PDF parsing task
    return source
