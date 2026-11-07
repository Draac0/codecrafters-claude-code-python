from typing import NotRequired, TypedDict


class SkillMetadata(TypedDict):
    name: str
    description: str
    context: NotRequired[str]
