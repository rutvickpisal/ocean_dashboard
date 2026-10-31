"""SQL queries and persistence operations for the API."""

from typing import Any

from ..db import fetch_all, fetch_one, where

Row = dict[str, Any]

SPECIES_COLUMNS = """
    id, common_name, scientific_name, category, diet,
    max_length_cm::float AS max_length_cm, conservation_status
"""
HABITAT_COLUMNS = """
    id, name, ocean, depth_zone,
    avg_temp_c::float AS avg_temp_c, latitude::float AS latitude, longitude::float AS longitude
"""


def check_database() -> Row | None:
    return fetch_one("SELECT 1 AS ok")


def list_species(
    limit: int,
    offset: int,
    category: str | None,
    conservation_status: str | None,
) -> list[Row]:
    conditions, params = [], {"limit": limit, "offset": offset}
    if category:
        conditions.append("category = %(category)s")
        params["category"] = category
    if conservation_status:
        conditions.append("conservation_status = %(status)s")
        params["status"] = conservation_status

    sql = f"""
        SELECT {SPECIES_COLUMNS}
        FROM species
        {where(conditions)}
        ORDER BY id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, params)


def get_species(species_id: int) -> Row | None:
    return fetch_one(
        f"SELECT {SPECIES_COLUMNS} FROM species WHERE id = %(id)s",
        {"id": species_id},
    )


def species_exists(species_id: int) -> bool:
    return fetch_one("SELECT 1 FROM species WHERE id = %(id)s", {"id": species_id}) is not None


def list_species_habitats(species_id: int, limit: int, offset: int) -> list[Row]:
    sql = """
        SELECT h.id AS habitat_id, h.name AS habitat_name, h.ocean, h.depth_zone,
               COUNT(*) AS times_seen,
               SUM(s.num_seen) AS total_individuals
        FROM sightings s
        JOIN habitats h ON h.id = s.habitat_id
        WHERE s.species_id = %(id)s
        GROUP BY h.id
        ORDER BY times_seen DESC, h.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, {"id": species_id, "limit": limit, "offset": offset})


def list_habitats(
    limit: int,
    offset: int,
    ocean: str | None,
    depth_zone: str | None,
) -> list[Row]:
    conditions, params = [], {"limit": limit, "offset": offset}
    if ocean:
        conditions.append("ocean = %(ocean)s")
        params["ocean"] = ocean
    if depth_zone:
        conditions.append("depth_zone = %(depth_zone)s")
        params["depth_zone"] = depth_zone

    sql = f"""
        SELECT {HABITAT_COLUMNS}
        FROM habitats
        {where(conditions)}
        ORDER BY id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, params)


def get_habitat(habitat_id: int) -> Row | None:
    return fetch_one(
        f"SELECT {HABITAT_COLUMNS} FROM habitats WHERE id = %(id)s",
        {"id": habitat_id},
    )


def habitat_exists(habitat_id: int) -> bool:
    return fetch_one("SELECT 1 FROM habitats WHERE id = %(id)s", {"id": habitat_id}) is not None


def list_habitat_species(habitat_id: int, limit: int, offset: int) -> list[Row]:
    sql = """
        SELECT sp.id AS species_id, sp.common_name, sp.category,
               COUNT(*) AS times_seen,
               SUM(s.num_seen) AS total_individuals
        FROM sightings s
        JOIN species sp ON sp.id = s.species_id
        WHERE s.habitat_id = %(id)s
        GROUP BY sp.id
        ORDER BY times_seen DESC, sp.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, {"id": habitat_id, "limit": limit, "offset": offset})


def list_observers(limit: int, offset: int, country: str | None) -> list[Row]:
    conditions, params = [], {"limit": limit, "offset": offset}
    if country:
        conditions.append("country = %(country)s")
        params["country"] = country

    sql = f"""
        SELECT id, full_name, email, country
        FROM observers
        {where(conditions)}
        ORDER BY id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, params)


def list_sightings(
    limit: int,
    offset: int,
    species_id: int | None,
    habitat_id: int | None,
    observer_id: int | None,
) -> list[Row]:
    conditions, params = [], {"limit": limit, "offset": offset}
    if species_id is not None:
        conditions.append("s.species_id = %(species_id)s")
        params["species_id"] = species_id
    if habitat_id is not None:
        conditions.append("s.habitat_id = %(habitat_id)s")
        params["habitat_id"] = habitat_id
    if observer_id is not None:
        conditions.append("s.observer_id = %(observer_id)s")
        params["observer_id"] = observer_id

    sql = f"""
        SELECT s.id, s.sighted_at, s.num_seen,
               sp.common_name AS species_name,
               h.name AS habitat_name, h.ocean,
               o.full_name AS observer_name
        FROM sightings s
        JOIN species   sp ON sp.id = s.species_id
        JOIN habitats  h  ON h.id  = s.habitat_id
        JOIN observers o  ON o.id  = s.observer_id
        {where(conditions)}
        ORDER BY s.sighted_at DESC, s.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, params)


def list_top_habitats(limit: int) -> list[Row]:
    sql = """
        SELECT h.id, h.name, h.ocean, h.depth_zone,
               COUNT(DISTINCT s.species_id) AS distinct_species,
               COUNT(*) AS total_sightings
        FROM habitats h
        JOIN sightings s ON s.habitat_id = h.id
        GROUP BY h.id
        ORDER BY distinct_species DESC, h.id
        LIMIT %(limit)s
    """
    return fetch_all(sql, {"limit": limit})


def list_never_sighted_species(limit: int, offset: int) -> list[Row]:
    sql = """
        SELECT sp.id, sp.common_name, sp.scientific_name, sp.category, sp.diet,
               sp.max_length_cm::float AS max_length_cm, sp.conservation_status
        FROM species sp
        LEFT JOIN sightings s ON s.species_id = sp.id
        WHERE s.id IS NULL
        ORDER BY sp.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    return fetch_all(sql, {"limit": limit, "offset": offset})


def list_top_observers(limit: int, min_sightings: int) -> list[Row]:
    sql = """
        SELECT o.id, o.full_name, o.country, COUNT(*) AS total_sightings
        FROM observers o
        JOIN sightings s ON s.observer_id = o.id
        GROUP BY o.id
        HAVING COUNT(*) >= %(min_sightings)s
        ORDER BY total_sightings DESC, o.id
        LIMIT %(limit)s
    """
    return fetch_all(sql, {"limit": limit, "min_sightings": min_sightings})


def list_endangered_by_ocean(days: int) -> list[Row]:
    sql = """
        SELECT h.ocean,
               COUNT(*) AS sightings,
               COUNT(DISTINCT s.species_id) AS distinct_species
        FROM sightings s
        JOIN species  sp ON sp.id = s.species_id
        JOIN habitats h  ON h.id  = s.habitat_id
        WHERE sp.conservation_status IN ('Endangered', 'Critically Endangered')
          AND s.sighted_at >= now() - make_interval(days => %(days)s::int)
        GROUP BY h.ocean
        ORDER BY sightings DESC
    """
    return fetch_all(sql, {"days": days})


def species_counts_by_category() -> list[Row]:
    sql = """
        SELECT category AS label, COUNT(*) AS count
        FROM species
        GROUP BY category
        ORDER BY count DESC
    """
    return fetch_all(sql)


def species_counts_by_status() -> list[Row]:
    sql = """
        SELECT conservation_status AS label, COUNT(*) AS count
        FROM species
        GROUP BY conservation_status
        ORDER BY count DESC
    """
    return fetch_all(sql)
