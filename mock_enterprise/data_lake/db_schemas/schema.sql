-- Database Schema for Financial Systems
-- Generated: 2023-10-27

-- Users table with client information
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Main financial table
CREATE TABLE term_sheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_sheet_id VARCHAR(50) UNIQUE NOT NULL,  -- Legacy string ID
    user_id UUID REFERENCES users(id),
    amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payment processing table
CREATE TABLE payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_sheet_id VARCHAR(50) REFERENCES term_sheets(term_sheet_id),
    payment_method VARCHAR(50),
    amount DECIMAL(15,2),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Index for performance
CREATE INDEX idx_term_sheets_user_id ON term_sheets(user_id);
CREATE INDEX idx_payment_transactions_term_sheet_id ON payment_transactions(term_sheet_id);