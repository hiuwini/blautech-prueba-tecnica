BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  full_name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
  document_type VARCHAR(100) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  content_type VARCHAR(255) NOT NULL,
  size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
  bucket_name VARCHAR(255) NOT NULL,
  object_key TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'UPLOADED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMPTZ NULL,
  CONSTRAINT documents_status_check CHECK (
    status IN ('UPLOADED', 'PROCESSING', 'COMPLIANT', 'NON_COMPLIANT', 'FAILED')
  ),
  CONSTRAINT documents_bucket_object_key_unique UNIQUE (bucket_name, object_key)
);

CREATE TABLE IF NOT EXISTS compliance_checks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  check_id UUID NOT NULL UNIQUE,
  status VARCHAR(32) NOT NULL,
  details TEXT NULL,
  checked_at TIMESTAMPTZ NOT NULL,
  raw_request_xml TEXT NULL,
  raw_response_xml TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT compliance_checks_status_check CHECK (
    status IN ('COMPLIANT', 'NON_COMPLIANT', 'FAILED')
  )
);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_set_updated_at ON documents;
DROP TRIGGER IF EXISTS set_documents_updated_at ON documents;

CREATE TRIGGER set_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_document_id
  ON compliance_checks (document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_checked_at
  ON compliance_checks (checked_at DESC);

COMMIT;
