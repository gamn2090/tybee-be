# Deployment Requirements Summary for Tybee Go

Below is a checklist of credentials, environment variables, and configuration items required from the client for deployment. Please review and provide the following:

## AWS & Storage
- AWS Account Access (for S3, etc.)
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_STORAGE_BUCKET_NAME
  - AWS_S3_REGION_NAME
  - AWS_S3_CUSTOM_DOMAIN (optional)
- or we can use local file storage

## Database
- RDS credentials (if using AWS RDS)
  - POSTGRES_DB
  - POSTGRES_USER
  - POSTGRES_PASSWORD
  - POSTGRES_HOST
  - POSTGRES_PORT

## Email Service (SMTP)
- SMTP server
- SMTP port
- SMTP username
- SMTP password
- Sender address (DEFAULT_FROM_EMAIL)

## Sentry (Error Monitoring)
- SENTRY_DSN (Sentry project DSN for error tracking)

## Extra
- Domain name
- GitHub repo access

---

**Please provide the above credentials and configuration details to proceed with deployment.**
