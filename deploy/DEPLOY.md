# Deployment Guide

Kahm-pew-terr uses Slack Socket Mode (persistent outbound WebSocket), so it must run as an **always-on container** — not a serverless function. No inbound ports are needed.

## Prerequisites

- Docker image built and pushed to your cloud's container registry
- Three secrets stored in your cloud's secret manager:
  - `SLACK_BOT_TOKEN` (xoxb-...)
  - `SLACK_APP_TOKEN` (xapp-...)
  - `PERPLEXITY_API_KEY` (pplx-...)

## Build & Push

```bash
# Build locally
docker build -t kahm-pew-terr .

# Tag and push (replace REGISTRY with your cloud registry URL)
docker tag kahm-pew-terr REGISTRY/kahm-pew-terr:latest
docker push REGISTRY/kahm-pew-terr:latest
```

---

## GCP — Cloud Run

Cloud Run supports always-on containers with `--min-instances=1` and `--no-cpu-throttling`.

### Quick deploy

```bash
# Store secrets in Secret Manager
echo -n "xoxb-..." | gcloud secrets create slack-bot-token --data-file=-
echo -n "xapp-..." | gcloud secrets create slack-app-token --data-file=-
echo -n "pplx-..." | gcloud secrets create perplexity-api-key --data-file=-

# Deploy from source (builds in Cloud Build)
gcloud run deploy kahm-pew-terr \
  --source . \
  --region us-central1 \
  --no-allow-unauthenticated \
  --min-instances=1 --max-instances=1 \
  --cpu=1 --memory=256Mi \
  --no-cpu-throttling \
  --set-secrets=SLACK_BOT_TOKEN=slack-bot-token:latest,SLACK_APP_TOKEN=slack-app-token:latest,PERPLEXITY_API_KEY=perplexity-api-key:latest
```

### CI/CD

Use `deploy/gcp/cloudbuild.yaml` with Cloud Build triggers.

### Cost estimate

~$5-10/month (1 always-on instance, minimal CPU).

---

## AWS — ECS Fargate

Fargate runs containers without managing servers. Good fit for always-on workloads.

### Quick deploy

```bash
# Create ECR repository
aws ecr create-repository --repository-name kahm-pew-terr

# Login, tag, push
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
docker tag kahm-pew-terr ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/kahm-pew-terr:latest
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/kahm-pew-terr:latest

# Store secrets in Secrets Manager
aws secretsmanager create-secret --name kahm-pew-terr/slack-bot-token --secret-string "xoxb-..."
aws secretsmanager create-secret --name kahm-pew-terr/slack-app-token --secret-string "xapp-..."
aws secretsmanager create-secret --name kahm-pew-terr/perplexity-api-key --secret-string "pplx-..."

# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/kahm-pew-terr

# Edit deploy/aws/task-definition.json (replace ACCOUNT_ID and REGION)
# Then register and run:
aws ecs register-task-definition --cli-input-json file://deploy/aws/task-definition.json
aws ecs create-cluster --cluster-name kahm-pew-terr
aws ecs create-service \
  --cluster kahm-pew-terr \
  --service-name bot \
  --task-definition kahm-pew-terr \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[SUBNET_ID],assignPublicIp=ENABLED}"
```

### Cost estimate

~$5-10/month (0.25 vCPU, 512MB Fargate).

---

## Azure — Container Apps

Container Apps is Azure's managed container service. Supports always-on with min replicas.

### Quick deploy

```bash
# Create resource group and environment
az group create --name kahm-pew-terr-rg --location eastus
az containerapp env create --name kahm-pew-terr-env --resource-group kahm-pew-terr-rg --location eastus

# Create ACR and push image
az acr create --name kahmpewterry --resource-group kahm-pew-terr-rg --sku Basic
az acr login --name kahmpewterry
docker tag kahm-pew-terr kahmpewterry.azurecr.io/kahm-pew-terr:latest
docker push kahmpewterry.azurecr.io/kahm-pew-terr:latest

# Deploy
az containerapp create \
  --name kahm-pew-terr \
  --resource-group kahm-pew-terr-rg \
  --environment kahm-pew-terr-env \
  --image kahmpewterry.azurecr.io/kahm-pew-terr:latest \
  --registry-server kahmpewterry.azurecr.io \
  --cpu 0.25 --memory 0.5Gi \
  --min-replicas 1 --max-replicas 1 \
  --secrets slack-bot-token="xoxb-..." slack-app-token="xapp-..." perplexity-api-key="pplx-..." \
  --env-vars \
    SLACK_BOT_TOKEN=secretref:slack-bot-token \
    SLACK_APP_TOKEN=secretref:slack-app-token \
    PERPLEXITY_API_KEY=secretref:perplexity-api-key \
    ADMIN_UID="" \
    HISTORY_DEPTH=10 \
    MSG_TRUNCATE_LENGTH=500
```

### Cost estimate

~$5-15/month (0.25 vCPU, 0.5 GiB always-on).

---

## Why not Cloudflare?

Cloudflare Workers/Pages have execution time limits (30s-15min) and cannot maintain the persistent outbound WebSocket that Socket Mode requires. Switching to HTTP webhook mode would enable Cloudflare, but requires a publicly accessible URL and different Slack app configuration.

---

## Scaling Notes

- **Max instances = 1**: Socket Mode maintains a single WebSocket connection. Multiple instances would create duplicate event processing.
- **Health checks**: Cloud Run and Container Apps may send HTTP health probes. The bot doesn't serve HTTP, but these platforms tolerate non-responsive health checks for always-on containers. If issues arise, add a simple health endpoint.
- **Restart policy**: All configs use auto-restart. The Slack SDK reconnects automatically on WebSocket drops.
