-- Created on first container start only (empty data volume).
CREATE DATABASE signals_ts;
CREATE DATABASE signals_rel;

\connect signals_ts
CREATE EXTENSION IF NOT EXISTS timescaledb;

\connect signals_rel
CREATE EXTENSION IF NOT EXISTS timescaledb;
