from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    status: str
    chunks: int
