# SECURITY FUNCTIONS FOR database.py
# Add these methods to the Database class

# ============================================================
# SECURITY: AUDIT LOGS
# ============================================================

def create_audit_log_table(self):
    """Create the audit_logs table if it doesn't exist."""
    if self.db_type == "supabase":
        # PostgreSQL syntax
        query = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                ip_address TEXT,
                status_code INTEGER,
                duration_ms REAL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                request_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint ON audit_logs(endpoint);
        """
    else:
        # SQLite syntax
        query = """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                ip_address TEXT,
                status_code INTEGER,
                duration_ms REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                request_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint ON audit_logs(endpoint);
        """
    
    # Execute the query
    if self.db_type == "supabase":
        import psycopg2
        conn = psycopg2.connect(self.pg_url)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(query)
        finally:
            conn.close()
    else:
        conn = self._get_conn()
        if self.db_path == ":memory:":
            conn.executescript(query)
        else:
            with conn:
                conn.executescript(query)


def create_audit_log(
    self,
    user_id: int = None,
    endpoint: str = "",
    method: str = "",
    ip_address: str = "",
    status_code: int = 0,
    duration_ms: float = 0.0,
    timestamp: str = None,
    user_agent: str = None,
    request_id: str = None
):
    """
    Create a new audit log entry.
    
    Args:
        user_id: ID of the user making the request
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        ip_address: Client IP address
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
        timestamp: ISO format timestamp
        user_agent: Client user agent string
        request_id: Unique request identifier
    """
    try:
        if timestamp:
            self._execute(
                """INSERT INTO audit_logs 
                   (user_id, endpoint, method, ip_address, status_code, 
                    duration_ms, timestamp, user_agent, request_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, endpoint, method, ip_address, status_code, 
                 duration_ms, timestamp, user_agent, request_id)
            )
        else:
            self._execute(
                """INSERT INTO audit_logs 
                   (user_id, endpoint, method, ip_address, status_code, 
                    duration_ms, user_agent, request_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, endpoint, method, ip_address, status_code, 
                 duration_ms, user_agent, request_id)
            )
    except Exception as e:
        logger.error(f"Error creating audit log: {e}")


def get_audit_logs(
    self,
    user_id: int = None,
    start_date: str = None,
    end_date: str = None,
    endpoint: str = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieve audit logs with optional filters.
    
    Args:
        user_id: Filter by user ID
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        endpoint: Filter by endpoint path
        limit: Maximum number of records
        offset: Pagination offset
    
    Returns:
        List of audit log records
    """
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    if endpoint:
        query += " AND endpoint = ?"
        params.append(endpoint)
    
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return self._fetchall(query, tuple(params))


def cleanup_old_audit_logs(self, days: int = 90) -> int:
    """
    Delete audit logs older than specified days.
    
    Args:
        days: Number of days to keep (default 90)
    
    Returns:
        Number of deleted records
    """
    if self.db_type == "supabase":
        query = """DELETE FROM audit_logs 
                   WHERE timestamp < NOW() - INTERVAL '%s days'"""
        query = query % days
    else:
        query = """DELETE FROM audit_logs 
                   WHERE timestamp < datetime('now', '-%d days')""" % days
    
    try:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(query)
        deleted = cursor.rowcount
        
        if self.db_path != ":memory:":
            conn.commit()
        
        return deleted
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        return 0


# ============================================================
# SECURITY: TOKEN BLACKLIST
# ============================================================

def create_token_blacklist_table(self):
    """Create the token_blacklist table if it doesn't exist."""
    if self.db_type == "supabase":
        query = """
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id SERIAL PRIMARY KEY,
                token_hash TEXT UNIQUE NOT NULL,
                expires_at BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_token_blacklist_hash ON token_blacklist(token_hash);
            CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);
        """
    else:
        query = """
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_token_blacklist_hash ON token_blacklist(token_hash);
            CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);
        """
    
    if self.db_type == "supabase":
        import psycopg2
        conn = psycopg2.connect(self.pg_url)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(query)
        finally:
            conn.close()
    else:
        conn = self._get_conn()
        if self.db_path == ":memory:":
            conn.executescript(query)
        else:
            with conn:
                conn.executescript(query)


def add_to_token_blacklist(self, token_hash: str, expires_at: int):
    """
    Add a token hash to the blacklist.
    
    Args:
        token_hash: SHA256 hash of the token
        expires_at: Unix timestamp when the token expires
    """
    try:
        self._execute(
            "INSERT OR IGNORE INTO token_blacklist (token_hash, expires_at) VALUES (?, ?)",
            (token_hash, expires_at)
        )
    except Exception as e:
        logger.error(f"Error adding token to blacklist: {e}")


def is_token_blacklisted(self, token_hash: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token_hash: SHA256 hash of the token
    
    Returns:
        True if the token is blacklisted
    """
    try:
        result = self._fetchone(
            "SELECT 1 FROM token_blacklist WHERE token_hash = ?",
            (token_hash,)
        )
        return result is not None
    except Exception as e:
        logger.error(f"Error checking token blacklist: {e}")
        return False


def cleanup_token_blacklist(self) -> int:
    """
    Remove expired tokens from the blacklist.
    
    Returns:
        Number of removed tokens
    """
    import time
    current_time = int(time.time())
    
    try:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM token_blacklist WHERE expires_at < ?",
            (current_time,)
        )
        deleted = cursor.rowcount
        
        if self.db_path != ":memory:":
            conn.commit()
        
        return deleted
    except Exception as e:
        logger.error(f"Error cleaning up token blacklist: {e}")
        return 0


# ============================================================
# SECURITY: REFRESH TOKENS
# ============================================================

def create_refresh_tokens_table(self):
    """Create the refresh_tokens table if it doesn't exist."""
    if self.db_type == "supabase":
        query = """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                family_id TEXT NOT NULL,
                device_info TEXT,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                expires_at BIGINT NOT NULL,
                revoked_at TIMESTAMPTZ,
                replaced_by_token_hash TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens(family_id);
        """
    else:
        query = """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                family_id TEXT NOT NULL,
                device_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at INTEGER NOT NULL,
                revoked_at DATETIME,
                replaced_by_token_hash TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash);
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens(family_id);
        """
    
    if self.db_type == "supabase":
        import psycopg2
        conn = psycopg2.connect(self.pg_url)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute(query)
        finally:
            conn.close()
    else:
        conn = self._get_conn()
        if self.db_path == ":memory:":
            conn.executescript(query)
        else:
            with conn:
                conn.executescript(query)


def store_refresh_token(
    self,
    user_id: int,
    token_hash: str,
    family_id: str,
    device_info: str = None,
    expires_at: int = None
):
    """
    Store a new refresh token.
    
    Args:
        user_id: User ID
        token_hash: SHA256 hash of the token
        family_id: Token family ID for rotation tracking
        device_info: Optional device information
        expires_at: Unix timestamp when the token expires
    """
    try:
        self._execute(
            """INSERT INTO refresh_tokens 
               (user_id, token_hash, family_id, device_info, expires_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, token_hash, family_id, device_info, expires_at)
        )
    except Exception as e:
        logger.error(f"Error storing refresh token: {e}")


def is_refresh_token_valid(self, token_hash: str, family_id: str) -> bool:
    """
    Check if a refresh token is valid (not revoked, not expired, correct family).
    
    Args:
        token_hash: SHA256 hash of the token
        family_id: Expected token family ID
    
    Returns:
        True if the token is valid
    """
    import time
    current_time = int(time.time())
    
    try:
        result = self._fetchone(
            """SELECT 1 FROM refresh_tokens 
               WHERE token_hash = ? 
                 AND family_id = ?
                 AND expires_at > ?
                 AND revoked_at IS NULL""",
            (token_hash, family_id, current_time)
        )
        return result is not None
    except Exception as e:
        logger.error(f"Error checking refresh token: {e}")
        return False


def revoke_refresh_token(self, token_hash: str, replaced_by: str = None):
    """
    Mark a refresh token as revoked.
    
    Args:
        token_hash: SHA256 hash of the token to revoke
        replaced_by: Optional hash of the new token that replaced this one
    """
    try:
        if self.db_type == "supabase":
            self._execute(
                """UPDATE refresh_tokens 
                   SET revoked_at = CURRENT_TIMESTAMP,
                       replaced_by_token_hash = ?
                   WHERE token_hash = ?""",
                (replaced_by, token_hash)
            )
        else:
            self._execute(
                """UPDATE refresh_tokens 
                   SET revoked_at = datetime('now'),
                       replaced_by_token_hash = ?
                   WHERE token_hash = ?""",
                (replaced_by, token_hash)
            )
    except Exception as e:
        logger.error(f"Error revoking refresh token: {e}")


def revoke_token_family(self, family_id: str):
    """
    Revoke all tokens in a family (security breach response).
    
    Args:
        family_id: Token family ID to revoke
    """
    try:
        if self.db_type == "supabase":
            self._execute(
                """UPDATE refresh_tokens 
                   SET revoked_at = CURRENT_TIMESTAMP
                   WHERE family_id = ?
                     AND revoked_at IS NULL""",
                (family_id,)
            )
        else:
            self._execute(
                """UPDATE refresh_tokens 
                   SET revoked_at = datetime('now')
                   WHERE family_id = ?
                     AND revoked_at IS NULL""",
                (family_id,)
            )
    except Exception as e:
        logger.error(f"Error revoking token family: {e}")


def revoke_all_user_refresh_tokens(self, user_id: int):
    """
    Revoke all refresh tokens for a user (logout all devices).
    
    Args:
        user_id: User ID
    """
    try:
        if self.db_type == "supabase":
            self._execute(
                """UPDATE refresh_tokens 
                   SET revoked_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?
                     AND revoked_at IS NULL""",
                (user_id,)
            )
        else:
            self._execute(
                """UPDATE refresh_tokens 
                   SET revoked_at = datetime('now')
                   WHERE user_id = ?
                     AND revoked_at IS NULL""",
                (user_id,)
            )
    except Exception as e:
        logger.error(f"Error revoking user refresh tokens: {e}")


def cleanup_expired_refresh_tokens(self) -> int:
    """
    Remove expired refresh tokens.
    
    Returns:
        Number of removed tokens
    """
    import time
    current_time = int(time.time())
    
    try:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM refresh_tokens WHERE expires_at < ?",
            (current_time,)
        )
        deleted = cursor.rowcount
        
        if self.db_path != ":memory:":
            conn.commit()
        
        return deleted
    except Exception as e:
        logger.error(f"Error cleaning up refresh tokens: {e}")
        return 0
