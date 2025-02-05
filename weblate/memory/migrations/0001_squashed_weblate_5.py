# Copyright © Michal Čihař <michal@weblate.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Generated by Django 4.2.5 on 2023-09-18 08:24

import django.db.models.deletion
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import migrations, models


def create_index(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        # This ensures that extensions are loaded into the session. Without that
        # the next ALTER database fails unless we're running as superuser (which
        # is allowed to set non existing parameters, so missing extension doesn't
        # matter)
        # See https://www.postgresql.org/message-id/6376.1533675236%40sss.pgh.pa.us
        schema_editor.execute("SELECT show_limit()")

        settings = schema_editor.connection.settings_dict

        schema_editor.execute(
            "ALTER ROLE {} SET pg_trgm.similarity_threshold = 0.5".format(
                schema_editor.quote_name(settings.get("ALTER_ROLE", settings["USER"]))
            )
        )
        # Install btree_gin for gin btree search and index
        cur = schema_editor.connection.cursor()
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'btree_gin'")
        if not cur.fetchone():
            schema_editor.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")

        # TODO: Find a better way for these indexes, used to avoid duplicate entries
        schema_editor.execute(
            "CREATE INDEX memory_source_index ON memory_memory USING HASH (source)"
        )
        schema_editor.execute(
            "CREATE INDEX memory_target_index ON memory_memory USING HASH (target)"
        )
        schema_editor.execute(
            "CREATE INDEX memory_origin_index ON memory_memory USING HASH (origin)"
        )
        schema_editor.execute(
            "CREATE INDEX memory_source_trgm ON memory_memory USING GIN "
            "(source gin_trgm_ops, target_language_id, source_language_id)"
        )
    elif vendor == "mysql":
        schema_editor.execute(
            "CREATE FULLTEXT INDEX memory_source_fulltext ON memory_memory(source)"
        )
        schema_editor.execute(
            "CREATE INDEX memory_lookup_index ON "
            "memory_memory(source(255), target(255), origin(255))"
        )
    else:
        raise ImproperlyConfigured(f"Unsupported database: {vendor}")


def drop_index(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        schema_editor.execute("DROP INDEX memory_source_trgm")
        schema_editor.execute("DROP INDEX memory_source_index")
        schema_editor.execute("DROP INDEX memory_target_index")
        schema_editor.execute("DROP INDEX memory_origin_index")
    elif vendor == "mysql":
        schema_editor.execute(
            "ALTER TABLE memory_memory DROP INDEX memory_source_fulltext"
        )
        schema_editor.execute(
            "ALTER TABLE memory_memory DROP INDEX memory_lookup_index"
        )
    else:
        raise ImproperlyConfigured(f"Unsupported database: {vendor}")


class Migration(migrations.Migration):
    replaces = [
        ("memory", "0001_squashed_0006_memory_update"),
        ("memory", "0007_use_trigram"),
        ("memory", "0008_adjust_similarity"),
        ("memory", "0009_pg_index"),
        ("memory", "0010_auto_20210506_1439"),
        ("memory", "0011_alter_memory_options"),
        ("memory", "0012_remove_blank"),
        ("memory", "0013_reindex"),
        ("memory", "0014_rename_index"),
        ("memory", "0015_remove_blank"),
        ("memory", "0016_remove_blank"),
    ]

    initial = True

    dependencies = [
        ("weblate_auth", "0002_squashed_weblate_5"),
        ("lang", "0001_squashed_weblate_5"),
        ("trans", "0001_squashed_weblate_5"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Memory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("source", models.TextField()),
                ("target", models.TextField()),
                ("origin", models.TextField()),
                ("from_file", models.BooleanField(default=False)),
                ("shared", models.BooleanField(default=False)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="trans.project",
                    ),
                ),
                (
                    "source_language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memory_source_set",
                        to="lang.language",
                    ),
                ),
                (
                    "target_language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memory_target_set",
                        to="lang.language",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Translation memory entry",
                "verbose_name_plural": "Translation memory entries",
            },
        ),
        migrations.RunPython(
            code=create_index,
            reverse_code=drop_index,
            atomic=False,
            elidable=False,
        ),
    ]
