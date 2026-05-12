# Cost Monitoring Backlog

- Add a monthly OpenAI billing-cycle rollup once the daily and 7-day alert thresholds have real baseline history.
- Add AWS cost monitoring as the next provider, keeping the dashboard as simple as the OpenAI usage view.
- When AWS is implemented, put local credentials in the ignored `homelab-monitor/.env` file first: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optional `AWS_REGION=us-east-1`.
- After the AWS collector shape is confirmed, add those AWS values to `service-secrets.yaml` and upload them through the managed GitHub Actions secret flow.
