-- Runs once, when the postgres volume is first created.
-- One database per service; each service creates its own tables on startup.
CREATE DATABASE auth;
CREATE DATABASE problems;
