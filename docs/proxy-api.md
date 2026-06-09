# Proxy API — `unit` parameter

Optional query parameter on two worker stats endpoints. Default is `gh` (GH/s); omitting `unit` is unchanged.

| `unit` | `hash_rate_unit` | Note |
|--------|------------------|------|
| `gh` (default) | `GH/s` | same as before |
| `mh` | `MH/s` | hashrate values × 1000 |

Auth: `Authorization: Bearer <API_TOKEN>`

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

---

## `GET /api/workers/timerange`

```bash
END=$(date -u +%s)
START=$((END - 86400))

curl -sS "${PROXY_URL}/api/workers/timerange?start_time=${START}&end_time=${END}&unit=mh" \
  -H "Authorization: Bearer ${API_TOKEN}"
```

`unit` affects `hash_rate_unit` and `hashrate` only. `shares` and `share_value` are unchanged.
