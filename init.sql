-- Enable the pgvector extension so the `embedding Vector(1536)` column on
-- the properties table works. This runs automatically on first DB init
-- because it is mounted into /docker-entrypoint-initdb.d.
CREATE EXTENSION IF NOT EXISTS vector;
