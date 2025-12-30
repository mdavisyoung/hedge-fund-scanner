# Streamlit Cloud Secrets Setup

## Format for Streamlit Cloud

When adding secrets in Streamlit Cloud (https://share.streamlit.io), use this format:

### In Streamlit Cloud UI:

Go to: **Your App → Settings → Secrets**

Add these secrets one by one:

```
XAI_API_KEY = "your-xai-api-key-here"
```

```
ALPACA_API_KEY = "PKD6UO5FVQ3T3KMZE3OVKV6UNE"
```

```
ALPACA_SECRET_KEY = "EbvHqEHW7rLBppmqYBs4nLfSPuN8GLrZV29iR8TyKmMC"
```

```
POLYGON_API_KEY = "SxSVtBXjH15jPsp94nrYnZ3fPMTpGvFr"
```

## Alternative: Copy-Paste Full TOML Format

If Streamlit Cloud allows pasting multiple secrets at once, you can paste this entire block:

```toml
XAI_API_KEY = "your-xai-api-key-here"
ALPACA_API_KEY = "your-alpaca-api-key-here"
ALPACA_SECRET_KEY = "your-alpaca-secret-key-here"
POLYGON_API_KEY = "your-polygon-api-key-here"
```

## Notes

- **DEXTER_API_URL**: Not needed for Streamlit Cloud (Dexter runs locally only)
- **SENDGRID_API_KEY**: Optional, only add if you want email notifications
- All values should be in quotes (`"..."`)
- Each secret on its own line with `KEY = "value"` format

## Security Reminder

⚠️ The `.streamlit/secrets.toml` file in your local repo is already in `.gitignore` and won't be committed. However, make sure you never commit actual API keys to your repository!

