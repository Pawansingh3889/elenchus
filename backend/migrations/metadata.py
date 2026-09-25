"""Migration-only constraints, kept out of ORM relationship join discovery."""

from sqlalchemy import ForeignKeyConstraint, MetaData, UniqueConstraint

from app.db.base import Base
from migrations.versions.ab47d902e631_workspace_isolation import REFERENCES, TABLES


def migration_metadata() -> MetaData:
    """Represent tenant constraints without making ORM relationships ambiguous.

    The revision supplies the explicit constraint inventory. When a future revision
    changes that inventory, update this migration view too. Copying the tables leaves
    the application's mapper metadata untouched.
    """
    metadata = MetaData(naming_convention=Base.metadata.naming_convention)
    for table in Base.metadata.tables.values():
        table.to_metadata(metadata)
    for name in TABLES:
        if name not in ("user_hats", "llm_requests", "interp_analyses"):
            metadata.tables[name].append_constraint(
                UniqueConstraint("workspace_id", "id", name=f"uq_{name}_workspace_id_id")
            )
    for name, column, parent in REFERENCES:
        metadata.tables[name].append_constraint(
            ForeignKeyConstraint(
                ["workspace_id", column],
                [f"{parent}.workspace_id", f"{parent}.id"],
                name=f"fk_{name}_{column}_workspace",
                deferrable=True,
                initially="DEFERRED",
            )
        )
    for table, column, parent in (
        ("survey_analysts", "template_id", "survey_templates"),
        ("survey_analysts", "analyst_id", "users"),
        ("survey_analysts", "assigned_by", "users"),
        ("survey_access_changes", "template_id", "survey_templates"),
        ("survey_access_changes", "analyst_id", "users"),
        ("survey_access_changes", "changed_by", "users"),
    ):
        ondelete = (
            "SET NULL" if table == "survey_access_changes" and column == "changed_by" else None
        )
        metadata.tables[table].append_constraint(
            ForeignKeyConstraint(
                ["workspace_id", column],
                [f"{parent}.workspace_id", f"{parent}.id"],
                name=f"fk_{table}_{column}_workspace",
                ondelete=ondelete,
                deferrable=True,
                initially="DEFERRED",
            )
        )
    return metadata
