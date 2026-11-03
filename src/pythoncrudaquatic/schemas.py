"""Response shapes used by FastAPI for validation and OpenAPI documentation."""

from datetime import datetime

from pydantic import BaseModel, Field


class Species(BaseModel):
    id: int
    common_name: str = Field(description="Everyday name, e.g. 'Spotted Octopus'")
    scientific_name: str = Field(description="Latin-style name (fake in this dataset)")
    category: str = Field(description="Fish, Shark, Ray, Mammal, Reptile, Mollusc, Cnidarian, Crustacean or Echinoderm")
    diet: str
    max_length_cm: float
    conservation_status: str = Field(description="Least Concern ... Critically Endangered")


class Habitat(BaseModel):
    id: int
    name: str
    ocean: str = Field(description="Pacific, Atlantic, Indian, Southern or Arctic")
    depth_zone: str = Field(description="Intertidal, Coral Reef, Open Ocean, Continental Shelf, Deep Sea or Abyssal")
    avg_temp_c: float | None
    latitude: float | None
    longitude: float | None


class Observer(BaseModel):
    id: int
    full_name: str
    email: str
    country: str


class SightingDetail(BaseModel):
    """One sighting with the readable names filled in (result of a 4-table JOIN)."""

    id: int
    sighted_at: datetime
    num_seen: int = Field(description="How many individuals were seen at once")
    species_name: str
    habitat_name: str
    ocean: str
    observer_name: str


class SpeciesHabitat(BaseModel):
    """A place where one particular species was seen."""

    habitat_id: int
    habitat_name: str
    ocean: str
    depth_zone: str
    times_seen: int = Field(description="Number of sighting records")
    total_individuals: int = Field(description="Sum of animals counted across those records")


class HabitatSpecies(BaseModel):
    """A species that was seen in one particular habitat."""

    species_id: int
    common_name: str
    category: str
    times_seen: int
    total_individuals: int


class TopHabitat(BaseModel):
    id: int
    name: str
    ocean: str
    depth_zone: str
    distinct_species: int = Field(description="How many different species were seen here")
    total_sightings: int


class TopObserver(BaseModel):
    id: int
    full_name: str
    country: str
    total_sightings: int


class OceanThreatSummary(BaseModel):
    ocean: str
    sightings: int = Field(description="Sightings of endangered species in this ocean")
    distinct_species: int = Field(description="How many different endangered species were involved")


class SpeciesCount(BaseModel):
    label: str
    count: int


class SpeciesSummary(BaseModel):
    total: int
    by_category: list[SpeciesCount]
    by_status: list[SpeciesCount]


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class AuthUser(BaseModel):
    id: int
    username: str
    email: str | None
    avatar_url: str | None
