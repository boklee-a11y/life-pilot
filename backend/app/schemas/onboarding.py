from pydantic import BaseModel


class ProfileUpdateRequest(BaseModel):
    job_category: str
    years_of_experience: int
    name: str | None = None
