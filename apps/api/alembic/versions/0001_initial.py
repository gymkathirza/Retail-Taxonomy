"""initial four-level taxonomy schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _timestamps():
    return [
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    ]


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_table(
        "departments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("zone_id", UUID(as_uuid=True), sa.ForeignKey("zones.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("zone_id", "name", name="uq_departments_zone_name"),
    )
    op.create_table(
        "categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("department_id", "name", name="uq_categories_department_name"),
    )
    op.create_table(
        "subcategories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("category_id", "name", name="uq_subcategories_category_name"),
    )
    op.execute(
        """
        CREATE VIEW sku_classification_paths AS
        SELECT
          s.id AS subcategory_id,
          z.name AS zone,
          d.name AS department,
          c.name AS category,
          s.name AS subcategory,
          z.name || ' > ' || d.name || ' > ' || c.name || ' > ' || s.name AS full_path,
          s.is_active AS is_active
        FROM subcategories s
        JOIN categories c ON c.id = s.category_id
        JOIN departments d ON d.id = c.department_id
        JOIN zones z ON z.id = d.zone_id;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS sku_classification_paths;")
    op.drop_table("subcategories")
    op.drop_table("categories")
    op.drop_table("departments")
    op.drop_table("zones")
