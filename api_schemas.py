from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mode: str = "explain"
    input: str | None = None
    examName: str | None = None
    examDate: str | None = None
    subjects: str | None = None
    studyHours: str | None = None


class DocumentQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: str = Field(max_length=2000)

    @field_validator("question", mode="before")
    @classmethod
    def question_must_not_be_blank(cls, value):
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            raise ValueError("Question must not be blank.")
        return value