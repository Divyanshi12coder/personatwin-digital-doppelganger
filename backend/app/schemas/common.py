from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.services.tags import MAX_TAGS, normalize_tags


def _clean_str_list(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        v = " ".join(v.split())
        if v and v.lower() not in {o.lower() for o in out}:
            out.append(v[:60])
    return out


TagList = Annotated[list[str], Field(default_factory=list, max_length=MAX_TAGS * 2), AfterValidator(normalize_tags)]
ShortList = Annotated[list[str], Field(default_factory=list, max_length=15), AfterValidator(_clean_str_list)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    detail: str
