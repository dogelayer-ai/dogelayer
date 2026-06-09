# DogeLayer Proxy API — Hashrate Unit Parameter

This document describes the optional `unit` query parameter on Proxy API worker statistics endpoints. Validators and third-party integrators use these endpoints to read miner hashrate from the subnet pool.

**Authentication**: `Authorization: Bearer <API_TOKEN>`

Validator-scoped tokens (`API_TOKENS`) and internal tokens (`INTERNAL_API_TOKENS`) are both accepted on the read endpoints below.

---

## Summary

| Endpoint | Method | `unit` support | Default |
|----------|--------|----------------|---------|
| `/api/workers/stats` | GET | Query param `unit` | `gh` (GH/s) |
| `/api/workers/timerange` | GET | Query param `unit` | `gh` (GH/s) |

**Backward compatible**: omitting `unit` behaves exactly as before — hashrate fields are returned in **GH/s** and `hash_rate_unit` is `"GH/s"`.

---

## Parameter: `unit`

| Value | `hash_rate_unit` in response | Divisor (from H/s) |
|-------|------------------------------|--------------------|
| `gh` (default) | `GH/s` | ÷ 10⁹ |
| `mh` | `MH/s` | ÷ 10⁶ |

Also accepted: `gh/s`, `mh/s` (case-insensitive).

Invalid values return **HTTP 400**: `Invalid unit. Use gh or mh`

### Conversion

```
display_value = hashrate_in_Hs / divisor
```

Example: 2.05 GH/s = 2050 MH/s (ratio 1000:1).

---

## GET `/api/workers/stats`

Per-worker statistics for fixed windows (`range=24h` or `range=7d`).

### Query parameters

| Param | Required | Description |
|-------|----------|-------------|
| `range` | No | `24h` or `7d` (default `24h`) |
| `worker` | No | Filter single worker |
| `workers` | No | Comma-separated hotkey prefix list |
| `state` | No | `ok` or `offline` |
| `page` / `page_size` | No | Pagination when filtering by `workers` |
| **`unit`** | No | `gh` (default) or `mh` |

### Example — default GH/s

```bash
curl -sS "${PROXY_URL}/api/workers/stats?range=24h" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

### Example — MH/s

```bash
curl -sS "${PROXY_URL}/api/workers/stats?range=24h&unit=mh" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

### Response fields affected by `unit`

Only hashrate-related fields change; **shares**, **share_value**, **online_hours**, **state**, and **last_share** are unchanged.

```json
{
  "doge": {
    "workers": {
      "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty": {
        "state": "ok",
        "last_share": 1780969152,
        "hash_rate_unit": "MH/s",
        "hash_rate_scoring": 0,
        "hash_rate_5m": 1374.39,
        "hash_rate_60m": 1073.74,
        "hash_rate_24h": 2049.85,
        "shares_5m": 6,
        "shares_60m": 69,
        "shares_24h": 3037,
        "share_value_5m": 162.13,
        "share_value_60m": 2742.78,
        "share_value_24h": 485990.79,
        "online_hours_7d": 167,
        "online_hours_30d": 183
      }
    }
  }
}
```

---

## GET `/api/workers/timerange`

Worker statistics for a custom Unix timestamp range (max 30 days).

### Query parameters

| Param | Required | Description |
|-------|----------|-------------|
| `start_time` | Yes | Unix timestamp (seconds), inclusive start |
| `end_time` | Yes | Unix timestamp (seconds), exclusive end |
| **`unit`** | No | `gh` (default) or `mh` |

### Example

```bash
END=$(date -u +%s)
START=$((END - 86400))

curl -sS "${PROXY_URL}/api/workers/timerange?start_time=${START}&end_time=${END}&unit=mh" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

### Response fields affected by `unit`

```json
{
  "btc": {
    "workers": {
      "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty.rig001": {
        "state": "ok",
        "last_share": 1780969152,
        "shares": 3037,
        "share_value": 485990.79,
        "hashrate": 2049.85,
        "hash_rate_unit": "MH/s"
      }
    }
  }
}
```

---

## Validator SDK (this repo)

The built-in `ProxyPoolAPI` client (`dogelayer/core/pool/proxy/api.py`) does **not** pass `unit` today. It continues to receive **GH/s** by default, which matches existing validator logic.

If you need MH/s in custom integrations, append `unit=mh` to the HTTP request as shown above. When reading the response, always check `hash_rate_unit` rather than assuming GH/s.

---

## Endpoints **not** affected

The `unit` parameter applies only to live worker stats and timerange queries. It does **not** apply to:

- `/api/workers/history-aggregate` (observer daily earnings — always Gh/s in `hashrate_unit`)
- `/api/pool/stats`
- `/api/workers/history/{worker}`

---

## Changelog

- **2026-06**: Added optional `unit=gh|mh` on `GET /api/workers/stats` and `GET /api/workers/timerange`. Default unchanged (`gh` / GH/s).
