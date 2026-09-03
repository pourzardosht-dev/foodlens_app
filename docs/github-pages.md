# GitHub Pages frontend

GitHub Pages can host the compiled Flutter Web frontend at no hosting cost. It cannot run FastAPI, PostgreSQL, MinIO or the Vision Provider. Those services remain on the VPS.

## Resulting architecture

```text
https://USERNAME.github.io/REPOSITORY
        Flutter Web on GitHub Pages
                    |
                    | HTTPS API requests
                    v
https://api.example.com
        reverse proxy on the VPS
                    |
                    v
http://127.0.0.1:18431
        FoodLens FastAPI container
```

GitHub supplies the `github.io` subdomain. A custom domain such as `foodlens.ir` must be registered separately, although GitHub Pages does not charge extra for attaching one.

## Repository setup

1. Push this project to a GitHub repository whose default branch is `main`.
2. In repository Settings > Pages, choose `GitHub Actions` as the source.
3. In Settings > Secrets and variables > Actions > Variables, create:

   ```text
   FOODLENS_API_URL=https://api.example.com
   ```

4. Push a change under `mobile/` or manually run the `Deploy Flutter Web to GitHub Pages` workflow.
5. Add the exact Pages origin to the VPS `.env`:

   ```dotenv
   CORS_ALLOWED_ORIGINS=https://USERNAME.github.io
   ```

   Origins do not include a path, so do not append `/REPOSITORY` to the CORS value.

## HTTPS requirement

GitHub Pages is served over HTTPS. Browsers block calls from it to a plain HTTP API, including `http://83.98.196.69:18431`. The API therefore needs a hostname and TLS certificate at the existing VPS reverse proxy. A raw IP is not the production API URL.

Free DNS and proxy services can manage DNS, but they do not grant ownership of a custom domain. For development, a temporary tunnel can be used; for production, register a domain and use a stable `api` subdomain.

## Custom domain

When a custom domain is attached to Pages, the Flutter base path changes from `/REPOSITORY/` to `/`. Update the workflow build command accordingly before enabling the custom domain.
