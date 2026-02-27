"""rename tables to metadata

Revision ID: 51a6a0dc27f3
Revises: 0d048e1cbb51
Create Date: 2026-02-27 17:10:11.515111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '51a6a0dc27f3'
down_revision: Union[str, Sequence[str], None] = '0d048e1cbb51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop foreign keys that point to old tables
    op.drop_constraint('character_moments_character_id_fkey', 'character_moments', type_='foreignkey')
    op.drop_constraint('character_moments_video_id_fkey', 'character_moments', type_='foreignkey')
    op.drop_constraint('video_screenshots_video_id_fkey', 'video_screenshots', type_='foreignkey')

    # 2. Rename tables
    op.rename_table('videos', 'video_metadata')
    op.rename_table('video_screenshots', 'character_screenshot_metadata')
    
    # 3. Recreate foreign keys to new tables
    op.create_foreign_key('character_moments_character_id_fkey', 'character_moments', 'character_screenshot_metadata', ['character_id'], ['id'])
    op.create_foreign_key('character_moments_video_id_fkey', 'character_moments', 'video_metadata', ['video_id'], ['id'])
    op.create_foreign_key('character_screenshot_metadata_video_id_fkey', 'character_screenshot_metadata', 'video_metadata', ['video_id'], ['id'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('character_moments_character_id_fkey', 'character_moments', type_='foreignkey')
    op.drop_constraint('character_moments_video_id_fkey', 'character_moments', type_='foreignkey')
    op.drop_constraint('character_screenshot_metadata_video_id_fkey', 'character_screenshot_metadata', type_='foreignkey')

    op.rename_table('video_metadata', 'videos')
    op.rename_table('character_screenshot_metadata', 'video_screenshots')

    op.create_foreign_key('character_moments_character_id_fkey', 'character_moments', 'video_screenshots', ['character_id'], ['id'])
    op.create_foreign_key('character_moments_video_id_fkey', 'character_moments', 'videos', ['video_id'], ['id'])
    op.create_foreign_key('video_screenshots_video_id_fkey', 'video_screenshots', 'videos', ['video_id'], ['id'])
