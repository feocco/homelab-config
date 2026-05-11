# OpenAI Cost Monitoring Next Steps

The OpenAI cost exporter is deployed as part of `homelab-monitor`, but it needs
an OpenAI Admin API key before it can report real costs.

## Needed Human Step

Create an OpenAI Admin API key from the OpenAI Platform organization admin
area. A normal project API key is not enough for the organization usage and
cost endpoints.

Once the Admin key exists, add it to the managed homelab secret flow:

1. Add `OPENAI_ADMIN_KEY` to `homelab-monitor/.env`.
2. Add `OPENAI_ADMIN_KEY` to the `homelab-monitor` section in
   `service-secrets.yaml`.
3. Run:

```bash
./scripts/generate-service-secret-workflow-env
./scripts/set-service-secrets homelab-monitor --repo feocco/homelab-config
./scripts/check-service-secrets
./scripts/homelab-deploy homelab-monitor --dry-run --deploy-base-dir /Users/feocco/homelab-config
```

4. Commit and push the updated secret manifest/workflow files.

After deployment, the Grafana dashboard should move from collector status
`Not collecting` to `Collecting`.

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
