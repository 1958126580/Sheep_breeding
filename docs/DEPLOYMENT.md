# Cloud Deployment Guide

This guide describes how to deploy the **International Top-tier Sheep Breeding System** to a Kubernetes cluster for SaaS operation.

## Prerequisites

- A running Kubernetes cluster (v1.24+)
- `kubectl` configured to communicate with the cluster
- A container registry (e.g., Docker Hub, ECR, ACR) to host images
- PostgreSQL and Redis instances (managed services recommended, e.g., RDS, ElastiCache)

## 1. Build and Push Images

```bash
# Backend
docker build -t your-registry/sheep-breeding-backend:latest ./backend
docker push your-registry/sheep-breeding-backend:latest

# Frontend
docker build -t your-registry/sheep-breeding-frontend:latest ./web-frontend
docker push your-registry/sheep-breeding-frontend:latest
```

## 2. Configure Secrets

Create a secret for database connections and other sensitive data:

```bash
kubectl create secret generic sheep-breeding-secrets \
  --namespace=sheep-breeding \
  --from-literal=database-url='postgresql://user:password@host:5432/dbname' \
  --from-literal=redis-url='redis://host:6379/0'
```

## 3. Deploy to Kubernetes

Apply the manifest files in the `k8s` directory:

```bash
# Create Namespace
kubectl apply -f k8s/namespace.yaml

# Deploy Backend
kubectl apply -f k8s/backend-deployment.yaml

# Deploy Frontend
kubectl apply -f k8s/frontend-deployment.yaml

# Create Ingress
kubectl apply -f k8s/ingress.yaml
```

## 4. Verification

Check the status of pods and services:

```bash
kubectl get pods -n sheep-breeding
kubectl get services -n sheep-breeding
```

## 5. Scaling

To scale the backend service for higher load:

```bash
kubectl scale deployment backend --replicas=5 -n sheep-breeding
```

## Cloud Provider Specifics

### AWS (EKS)

- Ensure AWS Load Balancer Controller is installed.
- Use `service.beta.kubernetes.io/aws-load-balancer-type: nlb` annotations if needed.

### Azure (AKS)

- Integration with Azure Container Registry (ACR) recommended.
- Use Azure Managed Identity for database access if possible.

### Alibaba Cloud (ACK)

- Configure SLB (Server Load Balancer) in annotations.
