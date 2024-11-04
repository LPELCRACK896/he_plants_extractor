from pydantic import BaseModel, validator
from typing import List, Optional

class Plant(BaseModel):
    name: Optional[str]
    source_pages: List[int]
    synonyms: Optional[List[str]]
    other_popular_names: Optional[List[str]]
    medical_used_parts: Optional[List[str]]
    description: Optional[str]
    habitat: Optional[str]
    obtaining: Optional[str]
    medicinal_uses_and_properties: Optional[str]
    experimental_and_clinical_pharmacology: Optional[str]

