-- server/resources/sql/list_extensions.sql
-- Lists installed extensions in the database as a JSON object

WITH extensions AS (
    SELECT
        extname AS name,
        extversion AS version,
        obj_description(e.oid, 'pg_extension') AS description
    FROM pg_extension e
    ORDER BY extname
)
SELECT jsonb_build_object(
    'extensions',
    jsonb_agg(
        jsonb_build_object(
            'name', name,
            'version', version,
            'description', description
        )
    )
) AS extension_list
FROM extensions;