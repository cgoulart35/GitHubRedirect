# GitHubRedirect

A tiny HTTP(S) redirect server: each configured port answers `GET /` with a
`302` to its URL. One process serves any number of redirects.

## Configuration (environment)

| Variable | Meaning |
|---|---|
| `REDIRECTS` | One redirect per line: `<name> <port> <url>`. Blank lines and `#` comments are ignored. Each redirect needs its own port. |
| `CERT_FILE`, `KEY_FILE` | Optional. If both point at existing files, it serves HTTPS; otherwise plain HTTP. |

```sh
REDIRECTS="
  docs     5010  https://example.github.io/docs/
  discord  5011  https://discord.gg/example
"
```

Logs go to stdout, one line per request, tagged with the redirect's name.

## Run with Docker

```sh
docker build -t github-redirect .
docker run --rm --network host \
  -e REDIRECTS="docs 5010 https://example.github.io/docs/" \
  github-redirect
```

For HTTPS, mount a cert and key and point `CERT_FILE`/`KEY_FILE` at them:

```sh
docker run --rm --network host \
  -e REDIRECTS="docs 5010 https://example.github.io/docs/" \
  -e CERT_FILE=/certs/server.crt -e KEY_FILE=/certs/server.key \
  -v /path/to/certs:/certs:ro \
  github-redirect
```

`--network host` lets the process bind each configured port directly, so the
port list lives only in `REDIRECTS`.

## Run without Docker

```sh
pip install -r requirements.txt
REDIRECTS="docs 5010 https://example.github.io/docs/" python main.py
```
