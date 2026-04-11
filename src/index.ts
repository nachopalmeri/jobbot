import { Hono } from 'hono';

interface Env {
	DB: D1Database;
}

interface BlogPost {
	id?: number;
	title: string;
	content: string;
	author: string;
	publishedAt?: string;
	createdAt?: string;
	updatedAt?: string;
}

const app = new Hono<{ Bindings: Env }>();

// CORS middleware
app.use('*', async (c, next) => {
	c.res.headers.set('Access-Control-Allow-Origin', '*');
	c.res.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
	c.res.headers.set('Access-Control-Allow-Headers', 'Content-Type');
	if (c.req.method === 'OPTIONS') {
		return c.text('', 204);
	}
	await next();
});

// GET /posts - List all posts (with optional pagination)
app.get('/posts', async (c) => {
	try {
		const url = new URL(c.req.url);
		const limit = parseInt(url.searchParams.get('limit') || '20');
		const offset = parseInt(url.searchParams.get('offset') || '0');

		const { results } = await c.env.DB.prepare(
			`SELECT id, title, content, author, publishedAt, createdAt, updatedAt 
			 FROM posts 
			 ORDER BY createdAt DESC 
			 LIMIT ? OFFSET ?`
		)
		.bind(limit, offset)
		.all();

		const { count } = await c.env.DB.prepare('SELECT COUNT(*) as count FROM posts').first() as { count: number };

		return c.json({
			success: true,
			data: results,
			meta: {
				total: count,
				limit,
				offset,
				hasMore: offset + results.length < count
			}
		});
	} catch (error) {
		console.error('Error fetching posts:', error);
		return c.json({
			success: false,
			error: 'Failed to fetch posts'
		}, 500);
	}
});

// GET /posts/:id - Get a single post
app.get('/posts/:id', async (c) => {
	try {
		const id = parseInt(c.req.param('id'));

		if (isNaN(id)) {
			return c.json({
				success: false,
				error: 'Invalid post ID'
			}, 400);
		}

		const post = await c.env.DB.prepare(
			`SELECT id, title, content, author, publishedAt, createdAt, updatedAt 
			 FROM posts 
			 WHERE id = ?`
		)
		.bind(id)
		.first();

		if (!post) {
			return c.json({
				success: false,
				error: 'Post not found'
			}, 404);
		}

		return c.json({
			success: true,
			data: post
		});
	} catch (error) {
		console.error('Error fetching post:', error);
		return c.json({
			success: false,
			error: 'Failed to fetch post'
		}, 500);
	}
});

// POST /posts - Create a new post
app.post('/posts', async (c) => {
	try {
		const body = await c.req.json<BlogPost>();

		// Validation
		if (!body.title || !body.content || !body.author) {
			return c.json({
				success: false,
				error: 'Missing required fields: title, content, author'
			}, 400);
		}

		if (body.title.length > 200) {
			return c.json({
				success: false,
				error: 'Title must be less than 200 characters'
			}, 400);
		}

		const publishedAt = body.publishedAt || new Date().toISOString();
		const now = new Date().toISOString();

		const result = await c.env.DB.prepare(
			`INSERT INTO posts (title, content, author, publishedAt, createdAt, updatedAt) 
			 VALUES (?, ?, ?, ?, ?, ?) 
			 RETURNING id`
		)
		.bind(body.title, body.content, body.author, publishedAt, now, now)
		.first();

		return c.json({
			success: true,
			message: 'Post created successfully',
			data: {
				id: result?.id,
				title: body.title,
				content: body.content,
				author: body.author,
				publishedAt,
				createdAt: now,
				updatedAt: now
			}
		}, 201);
	} catch (error) {
		console.error('Error creating post:', error);
		return c.json({
			success: false,
			error: 'Failed to create post'
		}, 500);
	}
});

// PUT /posts/:id - Update a post
app.put('/posts/:id', async (c) => {
	try {
		const id = parseInt(c.req.param('id'));

		if (isNaN(id)) {
			return c.json({
				success: false,
				error: 'Invalid post ID'
			}, 400);
		}

		const body = await c.req.json<Partial<BlogPost>>();

		// Check if post exists
		const existing = await c.env.DB.prepare('SELECT id FROM posts WHERE id = ?')
			.bind(id)
			.first();

		if (!existing) {
			return c.json({
				success: false,
				error: 'Post not found'
			}, 404);
		}

		// Validation
		if (body.title && body.title.length > 200) {
			return c.json({
				success: false,
				error: 'Title must be less than 200 characters'
			}, 400);
		}

		const updates: string[] = [];
		const values: (string | number | null)[] = [];

		if (body.title !== undefined) {
			updates.push('title = ?');
			values.push(body.title);
		}
		if (body.content !== undefined) {
			updates.push('content = ?');
			values.push(body.content);
		}
		if (body.author !== undefined) {
			updates.push('author = ?');
			values.push(body.author);
		}
		if (body.publishedAt !== undefined) {
			updates.push('publishedAt = ?');
			values.push(body.publishedAt);
		}

		if (updates.length === 0) {
			return c.json({
				success: false,
				error: 'No fields to update'
			}, 400);
		}

		updates.push('updatedAt = ?');
		values.push(new Date().toISOString());
		values.push(id);

		await c.env.DB.prepare(
			`UPDATE posts SET ${updates.join(', ')} WHERE id = ?`
		)
		.bind(...values)
		.run();

		// Fetch updated post
		const updated = await c.env.DB.prepare(
			`SELECT id, title, content, author, publishedAt, createdAt, updatedAt 
			 FROM posts 
			 WHERE id = ?`
		)
		.bind(id)
		.first();

		return c.json({
			success: true,
			message: 'Post updated successfully',
			data: updated
		});
	} catch (error) {
		console.error('Error updating post:', error);
		return c.json({
			success: false,
			error: 'Failed to update post'
		}, 500);
	}
});

// DELETE /posts/:id - Delete a post
app.delete('/posts/:id', async (c) => {
	try {
		const id = parseInt(c.req.param('id'));

		if (isNaN(id)) {
			return c.json({
				success: false,
				error: 'Invalid post ID'
			}, 400);
		}

		// Check if post exists
		const existing = await c.env.DB.prepare('SELECT id FROM posts WHERE id = ?')
			.bind(id)
			.first();

		if (!existing) {
			return c.json({
				success: false,
				error: 'Post not found'
			}, 404);
		}

		await c.env.DB.prepare('DELETE FROM posts WHERE id = ?')
			.bind(id)
			.run();

		return c.json({
			success: true,
			message: 'Post deleted successfully'
		});
	} catch (error) {
		console.error('Error deleting post:', error);
		return c.json({
			success: false,
			error: 'Failed to delete post'
		}, 500);
	}
});

// 404 handler
app.notFound((c) => {
	return c.json({
		success: false,
		error: 'Endpoint not found'
	}, 404);
});

// Error handler
app.onError((err, c) => {
	console.error('Unexpected error:', err);
	return c.json({
		success: false,
		error: 'Internal server error'
	}, 500);
});

export default app;
