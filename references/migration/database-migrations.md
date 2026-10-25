# Database migrations

**Last verified: 2026-10-24.**

## Rules

1. **Never** run schema or data migrations against production, or against any database that is not disposable or freshly backed up, during this skill.
2. Take and **verify** a backup (restore it once into a scratch DB) before running migrations in a shared test environment.
3. Read every migration before running it. Note destructive operations (`DROP`, `TRUNCATE`, column type narrowing, data rewrites) in the plan.
4. Prefer a copy: restore a sanitised dump into a throwaway container.

## Disposable test database (example)

```sh
docker run --rm -d --name mig-db -e MARIADB_ROOT_PASSWORD=test -e MARIADB_DATABASE=app -p 3307:3306 mariadb:11
# load an anonymised dump, point the app's TEST env at 127.0.0.1:3307, run migrations, then:
docker rm -f mig-db
```

Adapt to the engine and version that production uses. Major DB engine upgrades are a separate project.

## Verify

- Migration status before/after (framework command, see the framework reference).
- Schema diff: `mysqldump --no-data` / `pg_dump --schema-only` before vs after, compared with `diff`.
- Row counts for critical tables before/after.
- Application smoke test against the migrated DB.
- **Down/rollback**: if the framework supports reversible migrations, test rollback on the disposable DB. Many CMS updates (WordPress, Drupal, Magento, Moodle) are **one-way**, so rollback means restoring the backup.

## Recording

List each migration that ran in `migration.database_changes`. Mark the database test `blocked` if no disposable DB was available. Never `passed` because "migrations look fine".
