# Marketing Agent V2 - Deployment Guide

This guide covers deploying the Marketing Agent V2 to production environments.

## Pre-Deployment Checklist

- [ ] All environment variables configured in `.env`
- [ ] Database backups configured
- [ ] SSL/TLS certificates obtained
- [ ] External API keys (SendGrid, Buffer, etc.) obtained
- [ ] Monitoring and alerting set up
- [ ] Logging aggregation configured
- [ ] Disaster recovery plan documented

## Local Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd marketing_agent_v2

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Run migrations
make migrate

# Run tests
make test
```

## Docker Deployment

### Build Images

```bash
# Build custom image
docker build -t marketing-agent-v2:latest .

# Or use docker-compose
docker-compose build
```

### Deploy to Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml marketing-agent

# Check services
docker service ls
docker service logs marketing-agent_api
```

## Kubernetes Deployment

### Create Namespace

```bash
kubectl create namespace marketing-agent
```

### Create ConfigMap and Secrets

```bash
# ConfigMap for non-sensitive config
kubectl create configmap marketing-config \
  --from-literal=API_DEBUG=false \
  --from-literal=LOG_LEVEL=INFO \
  -n marketing-agent

# Secret for sensitive data
kubectl create secret generic marketing-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=REDIS_URL=redis://... \
  --from-literal=SENDGRID_API_KEY=... \
  -n marketing-agent
```

### Deploy PostgreSQL

```bash
# Using Helm
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  --namespace marketing-agent \
  --set auth.password=<password>
```

### Deploy Redis

```bash
helm install redis bitnami/redis \
  --namespace marketing-agent \
  --set auth.password=<password>
```

### Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/api-deployment.yaml -n marketing-agent
kubectl apply -f k8s/worker-deployment.yaml -n marketing-agent
kubectl apply -f k8s/scheduler-deployment.yaml -n marketing-agent
kubectl apply -f k8s/service.yaml -n marketing-agent
```

## Cloud Platform Deployment

### AWS Deployment

#### Using ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name marketing-agent

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster marketing-agent \
  --service-name marketing-api \
  --task-definition marketing-agent-api:1 \
  --desired-count 2
```

#### Using Elastic Beanstalk

```bash
# Initialize Elastic Beanstalk
eb init -p docker marketing-agent

# Create environment
eb create marketing-agent-prod

# Deploy
eb deploy
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build image
gcloud builds submit --tag gcr.io/PROJECT_ID/marketing-agent

# Deploy API
gcloud run deploy marketing-agent-api \
  --image gcr.io/PROJECT_ID/marketing-agent \
  --platform managed \
  --region us-central1
```

#### Using GKE

```bash
# Create cluster
gcloud container clusters create marketing-agent \
  --num-nodes 3 \
  --machine-type n1-standard-2

# Deploy
kubectl apply -f k8s/
```

### Azure Deployment

#### Using Container Instances

```bash
# Create resource group
az group create --name marketing-agent --location eastus

# Deploy container
az container create \
  --resource-group marketing-agent \
  --name marketing-api \
  --image marketing-agent-v2:latest \
  --environment-variables DATABASE_URL=... REDIS_URL=...
```

## Database Setup

### PostgreSQL

```bash
# Create database
createdb marketing_db

# Create user
createuser marketing_user

# Grant privileges
psql -c "ALTER USER marketing_user WITH PASSWORD 'password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE marketing_db TO marketing_user;"

# Run migrations
alembic upgrade head
```

### Backup Strategy

```bash
# Daily backup
pg_dump -U marketing_user marketing_db > backup_$(date +%Y%m%d).sql

# Or use automated backups (AWS RDS, Google Cloud SQL, etc.)
```

## Monitoring & Logging

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'marketing-agent'
    static_configs:
      - targets: ['localhost:8000']
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```bash
# Deploy ELK
docker-compose -f docker-compose.elk.yml up -d

# Configure Logstash to forward logs from application
```

### Datadog Integration

```bash
# Install Datadog agent
DD_AGENT_MAJOR_VERSION=7 DD_API_KEY=<key> bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_mac_os.sh)"

# Configure application monitoring
DD_SERVICE=marketing-agent DD_ENV=production DD_VERSION=2.0.0
```

## SSL/TLS Configuration

### Let's Encrypt with Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name marketing.example.com;

    ssl_certificate /etc/letsencrypt/live/marketing.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marketing.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Certbot Renewal

```bash
# Auto-renew certificates
certbot renew --quiet --no-self-upgrade
```

## Performance Tuning

### Database Connection Pooling

```python
# In database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Celery Configuration

```python
# In celery_app.py
celery_app.conf.update(
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True
)
```

### Redis Optimization

```bash
# In redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

## Security Hardening

### Environment Variables

```bash
# Never commit .env to version control
echo ".env" >> .gitignore

# Use secrets management (AWS Secrets Manager, HashiCorp Vault)
```

### Database Security

```bash
# Use strong passwords
# Restrict database access to application servers only
# Enable SSL connections to database
# Regular security updates
```

### API Security

```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

```bash
# Using Nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}
```

## Scaling Strategies

### Horizontal Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Or with Kubernetes
kubectl scale deployment marketing-api --replicas=3
```

### Load Balancing

```bash
# Using Nginx
upstream marketing_api {
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    location / {
        proxy_pass http://marketing_api;
    }
}
```

### Caching

```python
# Redis caching for expensive queries
from functools import lru_cache

@lru_cache(maxsize=128)
def get_trend_digest():
    # Expensive operation
    pass
```

## Disaster Recovery

### Backup & Restore

```bash
# Full backup
pg_dump -U marketing_user marketing_db | gzip > backup.sql.gz

# Restore
gunzip < backup.sql.gz | psql -U marketing_user marketing_db
```

### High Availability

```yaml
# Docker Swarm
version: '3.8'
services:
  api:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
```

## Maintenance

### Regular Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update Docker images
docker pull postgres:15
docker pull redis:7
```

### Database Maintenance

```bash
# Vacuum and analyze
psql -U marketing_user marketing_db -c "VACUUM ANALYZE;"

# Check table sizes
psql -U marketing_user marketing_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Troubleshooting

### Service Health Checks

```bash
# Check API health
curl http://localhost:8000/healthz

# Check database connection
docker-compose exec api python -c "from app.database import engine; engine.connect()"

# Check Redis connection
docker-compose exec redis redis-cli ping
```

### Log Analysis

```bash
# View application logs
docker-compose logs api

# Search logs for errors
docker-compose logs api | grep ERROR

# Follow logs in real-time
docker-compose logs -f api
```

### Performance Diagnostics

```bash
# Check database query performance
psql -U marketing_user marketing_db -c "EXPLAIN ANALYZE SELECT ..."

# Monitor Celery tasks
celery -A app.workers.celery_app inspect active

# Check Redis memory usage
redis-cli INFO memory
```

## Support & Documentation

For additional help, refer to:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

---

**Last Updated**: December 2025  
**Version**: 2.0.0
