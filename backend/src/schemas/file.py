from pydantic import BaseModel, field_validator

class FileSchema(BaseModel):
    path: str
    content_type: str

    @field_validator('content_type')
    def must_be_image(self, v: str) -> str:
        if not v.startswith('image/'):
            raise ValueError('Поддерживаются только изображения')
        return v