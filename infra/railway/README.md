# Railway Deployment

Deploy both services (web + api) for **prompt-showdown** on Railway.

## Setup

1. Create a new Railway project
2. Add two services from the same repo:

### Web Service (Next.js)
- **Service name**: `prompt-showdown-web`
- **Root Directory**: `apps/web`
- **Build Command**: `pnpm install && pnpm build`
- **Start Command**: `pnpm start`
- **Port**: `3000`

### API Service (FastAPI)
- **Service name**: `prompt-showdown-api`
- **Root Directory**: `services/api`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Environment Variables

Set these on the API service:

| Variable | Value |
|----------|-------|
| `B2_APPLICATION_KEY_ID` | Your B2 application key ID |
| `B2_APPLICATION_KEY` | Your B2 application key |
| `B2_BUCKET_NAME` | Your bucket name |
| `B2_REGION` | Your B2 region slug (e.g. `us-west-004`); the S3 endpoint is derived from it |
| `B2_PUBLIC_URL_BASE` | Optional friendly public URL base for public buckets |
| `NVIDIA_API_KEY` | Your NVIDIA NIM key (`nvapi-...`) for generation + judging |
| `API_CORS_ORIGINS` | Your web service URL (e.g., `https://prompt-showdown-web-production-xxx.up.railway.app`) |

Set this on the Web service:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your API service URL (e.g., `https://prompt-showdown-api-production-xxx.up.railway.app`) |
