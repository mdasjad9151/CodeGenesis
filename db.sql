-- Enable the pgcrypto extension to automatically generate UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- 1. USERS TABLE
-- ==========================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,

-- NULL for pure Google OAuth users who haven't set a password
hashed_password VARCHAR(255) NULL,

-- Track how the user originally signed up (e.g., 'credentials', 'google')
auth_source VARCHAR(50) NOT NULL DEFAULT 'credentials',

-- System flags
is_verified BOOLEAN NOT NULL DEFAULT FALSE,
is_active BOOLEAN NOT NULL DEFAULT TRUE,

-- Timestamps
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index on email since it will be looked up on every single registration/login
CREATE INDEX idx_users_email ON users (email);

-- ==========================================
-- 2. AUTH OTPS TABLE (For Registration & 2FA)
-- ==========================================
CREATE TABLE auth_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

-- Link directly to the user
user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,

-- The actual OTP code (hashed is safer, but plain text is common for short-lived numeric codes)
otp_code VARCHAR(10) NOT NULL,

-- Track what this OTP was issued for ('registration', 'login', 'password_reset')
purpose VARCHAR(50) NOT NULL DEFAULT 'registration',

-- Expiration timestamp
expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

-- Tracking usage to prevent replay attacks
is_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick lookups when verifying a code for a specific user
CREATE INDEX idx_auth_otps_user_code ON auth_otps (user_id, otp_code)
WHERE
    is_used = FALSE;




CREATE TABLE auth_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

-- Store a unique identifier from the JWT, not the raw token if possible
jti UUID NOT NULL UNIQUE,

-- Optional: store a hash of the refresh token for stronger security
token_hash VARCHAR(255),

    issued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    revoked_at TIMESTAMP WITH TIME ZONE,
    replaced_by_jti UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_refresh_token_expiry CHECK (expires_at > issued_at)
);

CREATE INDEX idx_auth_refresh_tokens_user_id ON auth_refresh_tokens (user_id);

CREATE INDEX idx_auth_refresh_tokens_expires_at ON auth_refresh_tokens (expires_at);



