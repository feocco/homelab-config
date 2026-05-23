# OpenAI Cost Monitoring Next Steps

The OpenAI cost exporter is deployed as part of `homelab-monitor`, but it needs
an OpenAI Admin API key with the `api.usage.read` scope before it can report
real costs.

## Needed Human Step

Create an OpenAI Admin API key from the OpenAI Platform organization admin
area and grant it the `api.usage.read` scope. A normal project API key, or an
Admin key without that scope, is not enough for the organization usage and cost
endpoints.

Once the Admin key exists, add it to the managed homelab secret flow:

1. Add or replace `OPENAI_ADMIN_KEY` in `services/homelab-monitor/.env`.
2. Run:

```bash
./scripts/generate-service-secret-workflow-env
./scripts/set-service-secrets homelab-monitor --repo feocco/homelab-config
./scripts/check-service-secrets
./scripts/homelab-deploy --host nasfeo homelab-monitor --dry-run --deploy-base-dir /Users/feocco/homelab-config
```

4. Commit and push the updated secret manifest/workflow files.

After deployment, the Grafana dashboard should move from collector status
`Not collecting` to `Collecting`. `OPENAI_ORG_ID` can stay blank for the
default personal organization unless OpenAI returns an organization selection
error.

## Dashboard

Grafana URL:

```text
http://nasfeo:3000/d/openai-cost-usage/openai-cost-usage
```

## Exported Metrics

- `openai_cost_usd{window="today|yesterday|last_7d|last_30d|month_to_date"}`
- `openai_cost_daily_usd{date="YYYY-MM-DD"}`
- `openai_cost_line_item_usd{project_id="...",line_item="..."}`
- `openai_usage_completions_requests{model="...",project_id="..."}`
- `openai_usage_completions_input_tokens{model="...",project_id="..."}`
- `openai_usage_completions_output_tokens{model="...",project_id="..."}`
- `openai_cost_exporter_up`
