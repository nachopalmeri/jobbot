-- Schema for blog posts table
-- Run this in your D1 database using:
-- wrangler d1 execute blog-db --file=./schema.sql

DROP TABLE IF EXISTS posts;

CREATE TABLE posts (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	title TEXT NOT NULL,
	content TEXT NOT NULL,
	author TEXT NOT NULL,
	publishedAt TEXT NOT NULL,
	createdAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updatedAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries by date
CREATE INDEX idx_posts_createdAt ON posts(createdAt DESC);
CREATE INDEX idx_posts_publishedAt ON posts(publishedAt DESC);
