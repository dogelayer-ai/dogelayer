# Proxy API — Validator worker endpoints

Auth: `Authorization: Bearer <API_TOKEN>`

Optional query parameter `unit` on worker stats endpoints. Default is `gh` (GH/s); omitting `unit` is unchanged.

| `unit` | `hash_rate_unit` | Note |
|--------|------------------|------|
| `gh` (default) | `GH/s` | same as before |
| `mh` | `MH/s` | hashrate values × 1000 |

---

## F2Pool observer link (`pool_observer_url`)

Both validator-facing worker endpoints return a **read-only F2Pool observer page URL** at the **top level** of the JSON response:

| Field | Type | Purpose |
|-------|------|---------|
| `pool_observer_url` | `string` | F2Pool **read-only** mining account page for upstream hashrate audit |

**What it is for**

- Lets validators (or operators) **manually compare** ClickHouse-based stats from the proxy with **F2Pool’s own dashboard** for the upstream LTC/DOGE pool account.
- **Does not affect scoring.** Validator weights still use `share_value` / worker stats from ClickHouse only.
- **No F2Pool API token required** on the validator side — this is a public observer link, not the F2Pool REST API.

**Which endpoints include it**

| Endpoint | Included |
|----------|----------|
| `GET /api/workers/stats` | Yes |
| `GET /api/workers/timerange` | Yes |

**Example response fragment** (`/api/workers/stats`):

```json
{
  "doge": {
    "workers": {
      "5D9jutP7...worker01": {
        "state": "ok",
        "hash_rate_5m": 2.19,
        "hash_rate_60m": 2.37,
        "hash_rate_24h": 2.18,
        "hash_rate_unit": "GH/s"
      }
    }
  },
  "pool_observer_url": "https://www.f2pool.com/mining-user-ltc/4c4d13e15249e898a3ba76d49c8aaa60?user_name=taosub"
}
```

**Default URL**

If the proxy operator does not override it, the subnet uses a built-in default observer URL for the shared upstream F2Pool account (`user_name=taosub`, LTC merged-mining view).

**Operator override (proxy only)**

Subnet owners / proxy operators may set on the **proxy API container** (not on the validator):

```bash
F2POOL_OBSERVER_URL=https://www.f2pool.com/mining-user-ltc/<account_hash>?user_name=<mining_user>
```

Validators do **not** need this env var — they receive the resolved URL in each API response.

**Audit workflow (recommended)**

1. Call `GET /api/workers/stats` or `GET /api/workers/timerange` as usual for scoring data.
2. Read `pool_observer_url` from the same response.
3. Open the link in a browser and compare **account / worker hashrate** on F2Pool with proxy/ClickHouse figures.
4. Large sustained gaps may indicate misconfiguration, submit floods, or stale data — see subnet incident docs on the proxy repo if needed.

---

## `GET /api/workers/stats`

```bash
# default GH/s
curl -sS "${PROXY_URL}/api/workers/stats" \
  -H "Authorization: Bearer ${API_TOKEN}"

# MH/s
curl -sS "${PROXY_URL}/api/workers/stats?unit=mh" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

`unit` affects `hash_rate_unit` and `hash_rate_5m` / `hash_rate_60m` / `hash_rate_24h` only.

Response also includes top-level `pool_observer_url` (see above).

---

## `GET /api/workers/timerange`

```bash
END=$(date -u +%s)
START=$((END - 86400))

curl -sS "${PROXY_URL}/api/workers/timerange?start_time=${START}&end_time=${END}&unit=mh" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

`unit` affects `hash_rate_unit` and `hashrate` only. `shares` and `share_value` are unchanged.

Worker data is under the top-level `btc.workers` key (legacy naming). `pool_observer_url` is at the **root** of the response, same as `/api/workers/stats`.
