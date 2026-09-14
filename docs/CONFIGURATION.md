# KubeLabs Platform Configuration Reference

## 1. Backend Environment Variables

The backend loads configuration via Pydantic `BaseSettings` from environment variables or `.env` files.

| Variable Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | String | `"KubeLabs SRE Platform"` | Application title reported in logs and OpenAPI specs |
| `VERSION` | String | `"1.0.0"` | Platform semantic version |
| `DATABASE_URL` | String | `"sqlite:///./kubelabs.db"` | Database connection string (SQLite WAL or PostgreSQL) |
| `SANDBOX_TTL_SECONDS`| Integer | `1800` | Default container sandbox TTL in seconds (30 minutes) |
| `ENABLE_PODMAN` | Boolean | `True` | Whether to attempt real rootless Podman container execution |
| `PODMAN_BINARY` | String | `"podman"` | Path to podman executable |
| `BASE_DIR` | Path | `.` | Root path of the KubeLabs monorepo |
| `LABS_DIR` | Path | `./labs` | Directory containing declarative YAML lab manifests |
| `CONTENT_DIR` | Path | `./content` | Directory containing curriculum tracks and assessments |

## 2. Frontend Configuration
Vite configuration resides in `apps/web/vite.config.ts`:
- Port: `5173`
- Reverse Proxy:
  - `/api` $\rightarrow$ `http://localhost:8000/api`
  - `/ws` $\rightarrow$ `ws://localhost:8000/ws`

## 3. Database Engine Configuration
For production deployments, replace the default SQLite database with PostgreSQL:
```bash
export DATABASE_URL="postgresql+psycopg2://kubelabs_user:secret@postgres-db:5432/kubelabs_prod"
```
