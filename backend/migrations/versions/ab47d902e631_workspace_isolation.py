"""Company ownership, row policies, and tenant-consistent references.

Revision ID: ab47d902e631
Revises: 5f1c7d9e2a48
"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "ab47d902e631"
down_revision = "5f1c7d9e2a48"
branch_labels = None
depends_on = None

LEGACY = UUID("00000000-0000-0000-0000-000000000001")
SCOPE = "nullif(current_setting('app.workspace_id', true), '')::uuid"
TABLES = (
    "users",
    "user_hats",
    "account_changes",
    "survey_templates",
    "survey_questions",
    "survey_runs",
    "answers",
    "run_messages",
    "llm_spans",
    "llm_requests",
    "prompt_versions",
    "prompt_activations",
    "embedding_vectors",
    "interp_analyses",
    "answer_labels",
    "corpus_labels",
    "judge_runs",
    "judge_verdicts",
    "eval_runs",
)
# Database constraints supplement the existing single-column ORM relationships.
# Deferred checks retain existing CASCADE and SET NULL semantics without introducing
# ambiguous ORM joins. Trace links remain deliberately FK-free because they are saved
# independently while the run transaction can still hold a lock.
REFERENCES = (
    ("users", "created_by", "users"),
    ("user_hats", "user_id", "users"),
    ("account_changes", "user_id", "users"),
    ("account_changes", "changed_by", "users"),
    ("survey_templates", "created_by", "users"),
    ("survey_templates", "published_by", "users"),
    ("survey_templates", "audience_user_id", "users"),
    ("survey_questions", "template_id", "survey_templates"),
    ("survey_runs", "template_id", "survey_templates"),
    ("survey_runs", "respondent_id", "users"),
    ("answers", "run_id", "survey_runs"),
    ("answers", "answered_by", "users"),
    ("run_messages", "run_id", "survey_runs"),
    ("run_messages", "answer_id", "answers"),
    ("prompt_versions", "created_by", "users"),
    ("prompt_activations", "activated_by", "users"),
    ("answer_labels", "answer_id", "answers"),
    ("answer_labels", "labelled_by", "users"),
    ("corpus_labels", "labelled_by", "users"),
    ("judge_runs", "run_id", "survey_runs"),
    ("judge_verdicts", "judge_run_id", "judge_runs"),
    ("judge_verdicts", "answer_id", "answers"),
    ("eval_runs", "run_id", "survey_runs"),
    ("eval_runs", "created_by", "users"),
)


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.execute(
        sa.text("INSERT INTO workspaces (id, name) VALUES (:id, :name)").bindparams(
            id=LEGACY, name="Legacy workspace"
        )
    )
    for table in TABLES:
        op.add_column(table, sa.Column("workspace_id", sa.Uuid(), nullable=True))
        op.execute(sa.text(f"UPDATE {table} SET workspace_id = :id").bindparams(id=LEGACY))
        op.alter_column(table, "workspace_id", nullable=False, server_default=sa.text(SCOPE))
        op.create_foreign_key(
            f"fk_{table}_workspace_id_workspaces", table, "workspaces", ["workspace_id"], ["id"]
        )
        op.create_index(f"ix_{table}_workspace_id", table, ["workspace_id"])
        if table not in ("user_hats", "llm_requests", "interp_analyses"):
            op.create_unique_constraint(
                f"uq_{table}_workspace_id_id", table, ["workspace_id", "id"]
            )
    for table, column, parent in REFERENCES:
        op.create_foreign_key(
            f"fk_{table}_{column}_workspace",
            table,
            parent,
            ["workspace_id", column],
            ["workspace_id", "id"],
            deferrable=True,
            initially="DEFERRED",
        )
    op.drop_constraint("uq_prompt_versions_name", "prompt_versions", type_="unique")
    op.create_unique_constraint(
        "uq_prompt_versions_workspace_name", "prompt_versions", ["workspace_id", "name"]
    )
    op.drop_constraint("uq_embedding_vectors_digest_model", "embedding_vectors", type_="unique")
    op.create_unique_constraint(
        "uq_embedding_vectors_workspace_digest_model",
        "embedding_vectors",
        ["workspace_id", "digest", "model"],
    )
    op.drop_constraint("uq_corpus_labels_fixture_answer", "corpus_labels", type_="unique")
    op.create_unique_constraint(
        "uq_corpus_labels_workspace_fixture_answer",
        "corpus_labels",
        ["workspace_id", "fixture", "answer_index"],
    )
    for table in (*TABLES, "workspaces"):
        column = "id" if table == "workspaces" else "workspace_id"
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY workspace_rows ON {table} USING ({column} = {SCOPE}) "
            f"WITH CHECK ({column} = {SCOPE})"
        )
    # Only authenticated identity bootstrap uses these transaction-local hints. This
    # additional SELECT policy cannot authorize INSERT, UPDATE, or DELETE.
    op.execute(
        "CREATE POLICY authenticated_identity ON users FOR SELECT USING ("
        "id = nullif(current_setting('app.actor_id', true), '')::uuid OR "
        "email = nullif(current_setting('app.verified_email', true), '') OR "
        "microsoft_id = nullif(current_setting('app.microsoft_id', true), ''))"
    )


def downgrade() -> None:
    # Combining tenants would collide on cache keys, prompt names, and label keys.
    # Refuse even when today's keys happen not to collide: it would erase the boundary.
    count = op.get_bind().scalar(sa.text("SELECT count(*) FROM workspaces"))
    if count != 1:
        raise RuntimeError("Workspace isolation cannot be removed from a multi-company database.")
    for table in (*TABLES, "workspaces"):
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY workspace_rows ON {table}")
    op.execute("DROP POLICY authenticated_identity ON users")
    for table, column, _parent in reversed(REFERENCES):
        op.drop_constraint(f"fk_{table}_{column}_workspace", table, type_="foreignkey")
    op.drop_constraint("uq_prompt_versions_workspace_name", "prompt_versions", type_="unique")
    op.create_unique_constraint("uq_prompt_versions_name", "prompt_versions", ["name"])
    op.drop_constraint(
        "uq_embedding_vectors_workspace_digest_model", "embedding_vectors", type_="unique"
    )
    op.create_unique_constraint(
        "uq_embedding_vectors_digest_model", "embedding_vectors", ["digest", "model"]
    )
    op.drop_constraint("uq_corpus_labels_workspace_fixture_answer", "corpus_labels", type_="unique")
    op.create_unique_constraint(
        "uq_corpus_labels_fixture_answer", "corpus_labels", ["fixture", "answer_index"]
    )
    for table in reversed(TABLES):
        op.drop_column(table, "workspace_id")
    op.drop_table("workspaces")
