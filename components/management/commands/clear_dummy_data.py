import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from components.models import Component, ReuseRecord, ComponentUsage, ComponentKeyword, ComponentWord

class Command(BaseCommand):
    help = "Delete all dummy Component entries and associated records/files from the system."

    def handle(self, *args, **options):
        # 1. Delete via ORM on the configured database
        count = Component.objects.count()
        self.stdout.write(f"Found {count} component(s) to remove.")

        # Delete related tables explicitly to be thorough and clean
        ComponentWord.objects.all().delete()
        ComponentKeyword.objects.all().delete()
        ReuseRecord.objects.all().delete()
        ComponentUsage.objects.all().delete()
        deleted_count, _ = Component.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} component(s) and related records from primary database."))

        # 2. Also clean local sqlite backup if it exists, to prevent any fallback reappearance
        for db_name in ['supabase_catalogue.sqlite3']:
            db_path = settings.BASE_DIR / db_name
            if db_path.exists():
                try:
                    import sqlite3
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='components_component'")
                    if cursor.fetchone():
                        cursor.execute("DELETE FROM components_component")
                        cursor.execute("DELETE FROM components_reuserecord")
                        cursor.execute("DELETE FROM components_componentusage")
                        cursor.execute("DELETE FROM components_componentkeyword")
                        conn.commit()
                        self.stdout.write(f"Cleared local SQLite backup: {db_name}")
                    conn.close()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Note: local file {db_name} cleanup skipped: {e}"))

        # 3. Clean uploaded media component sample files
        media_comp_dir = settings.MEDIA_ROOT / 'components'
        if media_comp_dir.exists():
            for item in media_comp_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    try:
                        item.unlink()
                    except OSError:
                        pass
            self.stdout.write(self.style.SUCCESS("Cleaned media components directory."))

        self.stdout.write(self.style.SUCCESS("Done! All dummy components removed."))
