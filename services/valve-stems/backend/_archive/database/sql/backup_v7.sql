--
-- PostgreSQL database cluster dump
--

-- Started on 2024-10-29 19:24:02

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'SCRAM-SHA-256$4096:3vWdRK8lFewemddC3Wu4mg==$MS/nc6Gk3bVHLkeXCmd/55bIEL04BX3Yw15emT+3DDQ=:Q0kZwivqeBO6daiwqVE6ooYGa2a5zMhkEFvht/IsYZQ=';

--
-- User Configurations
--








-- Completed on 2024-10-29 19:24:02

--
-- PostgreSQL database cluster dump complete
--

