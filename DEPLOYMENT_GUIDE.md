# Kubernetes Deployment Guide for RAG Application

## Prerequisites
- AWS Account with ECR access
- Kubernetes cluster (EKS, Minikube, or any K8s cluster)
- kubectl installed and configured
- Docker image pushed to ECR
- AWS credentials with Bedrock access

## Step-by-Step Deployment Instructions

### Step 1: Verify Your Kubernetes Cluster
```bash
# Check if kubectl is configured
kubectl cluster-info

# Check nodes
kubectl get nodes
```

### Step 2: Create AWS Credentials Secret
Before deploying, create a Kubernetes secret with your AWS credentials:

```bash
# Replace with your actual AWS credentials
kubectl create secret generic aws-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID \
  --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
```

**Verify the secret was created:**
```bash
kubectl get secrets
kubectl describe secret aws-credentials
```

### Step 3: Verify Docker Image in ECR
Make sure your Docker image is available in ECR:

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 020866158197.dkr.ecr.us-east-1.amazonaws.com

# List images in your repository
aws ecr describe-images --repository-name flask-app --region us-east-1
```

### Step 4: Deploy the Application
Apply the deployment configuration:

```bash
# Navigate to project directory
cd RAG_Project_AWS_Bedrock

# Apply the deployment
kubectl apply -f deployment.yaml
```

**Expected output:**
```
deployment.apps/rag-app created
service/rag-app-service created
```

### Step 5: Verify Deployment Status
Check if pods are running:

```bash
# Check deployment status
kubectl get deployments

# Check pods
kubectl get pods

# Check detailed pod status
kubectl describe pods

# View pod logs (replace POD_NAME with actual pod name)
kubectl logs <POD_NAME>
```

### Step 6: Check Service Status
Verify the LoadBalancer service:

```bash
# Get service details
kubectl get services

# Get detailed service info
kubectl describe service rag-app-service
```

**Wait for External IP:**
The LoadBalancer may take a few minutes to provision. Keep checking:
```bash
kubectl get service rag-app-service --watch
```

### Step 7: Access the Application
Once the EXTERNAL-IP is assigned:

```bash
# Get the external IP
kubectl get service rag-app-service

# Access the application
# Open browser to: http://<EXTERNAL-IP>
```

For example: `http://a1b2c3d4e5f6.us-east-1.elb.amazonaws.com`

### Step 8: Test the Application
1. Open the external URL in your browser
2. You should see the Streamlit RAG application
3. Try asking a question to verify it's working

## Troubleshooting Commands

### Check Pod Logs
```bash
# List all pods
kubectl get pods

# View logs for a specific pod
kubectl logs rag-app-<pod-id>

# Follow logs in real-time
kubectl logs -f rag-app-<pod-id>

# View previous pod logs (if pod crashed)
kubectl logs rag-app-<pod-id> --previous
```

### Debug Pod Issues
```bash
# Describe pod for detailed information
kubectl describe pod rag-app-<pod-id>

# Execute commands inside the pod
kubectl exec -it rag-app-<pod-id> -- /bin/bash

# Check environment variables
kubectl exec rag-app-<pod-id> -- env
```

### Check Resource Usage
```bash
# Check pod resource usage
kubectl top pods

# Check node resource usage
kubectl top nodes
```

### Common Issues and Solutions

#### Issue 1: ImagePullBackOff
**Symptom:** Pod status shows `ImagePullBackOff`

**Solution:**
```bash
# Verify ECR image exists
aws ecr describe-images --repository-name flask-app --region us-east-1

# Check if image tag is correct in deployment.yaml
# Ensure ECR permissions are set correctly
```

#### Issue 2: CrashLoopBackOff
**Symptom:** Pod keeps restarting

**Solution:**
```bash
# Check pod logs
kubectl logs rag-app-<pod-id>

# Common causes:
# - Missing AWS credentials
# - Incorrect environment variables
# - Application errors
```

#### Issue 3: Pending External IP
**Symptom:** Service EXTERNAL-IP shows `<pending>`

**Solution:**
- Wait 2-5 minutes for LoadBalancer provisioning
- Check if your cluster supports LoadBalancer type
- For Minikube, use: `minikube tunnel` in a separate terminal

#### Issue 4: AWS Credentials Error
**Symptom:** Application can't access AWS Bedrock

**Solution:**
```bash
# Verify secret exists
kubectl get secret aws-credentials

# Recreate secret with correct credentials
kubectl delete secret aws-credentials
kubectl create secret generic aws-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=YOUR_KEY \
  --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_SECRET

# Restart pods to pick up new secret
kubectl rollout restart deployment rag-app
```

## Scaling the Application

### Scale Up
```bash
# Scale to 5 replicas
kubectl scale deployment rag-app --replicas=5

# Verify scaling
kubectl get pods
```

### Scale Down
```bash
# Scale to 1 replica
kubectl scale deployment rag-app --replicas=1
```

### Auto-scaling (Optional)
```bash
# Create horizontal pod autoscaler
kubectl autoscale deployment rag-app --cpu-percent=70 --min=3 --max=10

# Check autoscaler status
kubectl get hpa
```

## Updating the Application

### Update Docker Image
```bash
# After pushing new image to ECR
kubectl set image deployment/rag-app rag-app=020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app:new-tag

# Or edit deployment
kubectl edit deployment rag-app

# Check rollout status
kubectl rollout status deployment/rag-app
```

### Rollback Deployment
```bash
# View rollout history
kubectl rollout history deployment/rag-app

# Rollback to previous version
kubectl rollout undo deployment/rag-app

# Rollback to specific revision
kubectl rollout undo deployment/rag-app --to-revision=2
```

## Cleanup

### Delete Everything
```bash
# Delete deployment and service
kubectl delete -f deployment.yaml

# Delete secret
kubectl delete secret aws-credentials

# Verify deletion
kubectl get all
```

## Monitoring and Maintenance

### View Events
```bash
# View cluster events
kubectl get events --sort-by=.metadata.creationTimestamp

# Watch events in real-time
kubectl get events --watch
```

### Health Checks
```bash
# Check deployment health
kubectl get deployment rag-app

# Check pod health
kubectl get pods -l app=rag-app

# Check service endpoints
kubectl get endpoints rag-app-service
```

## Configuration Summary

### Current Deployment Configuration:
- **Application:** RAG with AWS Bedrock (Streamlit)
- **Replicas:** 3 pods
- **Container Port:** 8501 (Streamlit)
- **Service Port:** 80 (HTTP)
- **Service Type:** LoadBalancer
- **Resources:**
  - Memory Request: 512Mi
  - Memory Limit: 1Gi
  - CPU Request: 500m
  - CPU Limit: 1 core

### Environment Variables:
- `AWS_ACCESS_KEY_ID` - From secret
- `AWS_SECRET_ACCESS_KEY` - From secret
- `AWS_DEFAULT_REGION` - us-east-1

## Next Steps
1. Set up monitoring (Prometheus/Grafana)
2. Configure ingress for custom domain
3. Set up SSL/TLS certificates
4. Implement CI/CD pipeline
5. Configure backup and disaster recovery

## Support
For issues, check:
- Pod logs: `kubectl logs <pod-name>`
- Pod events: `kubectl describe pod <pod-name>`
- Service status: `kubectl describe service rag-app-service`