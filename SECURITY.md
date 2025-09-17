# Security Guidelines

- **Never commit secrets**. Hugging Face tokens, SMTP credentials, and mobile
  configuration secrets must be supplied via environment variables or `.env`
  files that stay out of version control.
- Rotate Hugging Face tokens immediately if they are exposed and invalidate any
  leaked SMTP credentials.
- Limit sharing of `.env` files and prefer using password managers or secret
  stores for distribution.
- When testing, use `DAILYNEWS_SKIP_HF=1` to avoid unexpected calls to external
  services.
- Review and prune dependencies regularly. Apply security updates for Python,
  Flutter, and Node.js environments as they become available.
