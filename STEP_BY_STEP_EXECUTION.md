# Complete Step-by-Step Execution Guide

This guide walks you through the entire process from setup to deployment.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS Account with admin access
- [ ] GitHub account
- [ ] Git installed on your computer
- [ ] AWS CLI installed and configured
- [ ] kubectl installed
- [ ] Docker installed (for local testing)
- [ ] Code editor (VS Code recommended)

---

## 🚀 PHASE 1: AWS Setup

### Step 1.1: Create ECR Repository

```bash
# Login to AWS Console or use CLI
aws ecr create-repository \
    --repository-name flask-app \
    --region us-east-1

# Note down the repository URI
# Example: 020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app
```

**Expected Output:**
```json
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-east-1:020866158197:repository/flask-app",
        "registryId": "020866158197",
        "repositoryName": "flask-app",
        "repositoryUri": "020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app"
    }
}
```

### Step 1.2: Create EKS Cluster

**Option A: Using AWS Console**
1. Go to AWS Console → EKS
2. Click "Create cluster"
3. Name: `rag-app-cluster`
4. Kubernetes version: 1.28 or latest
5. Create cluster (takes 10-15 minutes)

**Option B: Using eksctl (Recommended)**
```bash
# Install eksctl if not installed
# Windows: choco install eksctl
# Mac: brew install eksctl
# Linux: See https://eksctl.io/

# Create cluster
eksctl create cluster \
    --name rag-app-cluster \
    --region us-east-1 \
    --nodegroup-name standard-workers \
    --node-type t3.medium \
    --nodes 3 \
    --nodes-min 1 \
    --nodes-max 4 \
    --managed

# This takes 15-20 minutes
```

**Verify cluster creation:**
```bash
aws eks list-clusters --region us-east-1
aws eks describe-cluster --name rag-app-cluster --region us-east-1
```

### Step 1.3: Configure kubectl for EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig \
    --name rag-app-cluster \
    --region us-east-1

# Verify connection
kubectl cluster-info
kubectl get nodes
```

**Expected Output:**
```
NAME                                          STATUS   ROLES    AGE   VERSION
ip-192-168-1-1.us-east-1.compute.internal    Ready    <none>   5m    v1.28.x
ip-192-168-1-2.us-east-1.compute.internal    Ready    <none>   5m    v1.28.x
ip-192-168-1-3.us-east-1.compute.internal    Ready    <none>   5m    v1.28.x
```

### Step 1.4: Get AWS Credentials

```bash
# If you don't have access keys, create them
aws iam create-access-key --user-name your-username

# Or view existing credentials
cat ~/.aws/credentials
```

**Save these values:**
- AWS_ACCESS_KEY_ID: `AKIA...`
- AWS_SECRET_ACCESS_KEY: `your-secret-key`
- AWS_REGION: `us-east-1`

---

## 🔐 PHASE 2: GitHub Setup

### Step 2.1: Fork/Clone Repository

```bash
# If you haven't cloned yet
cd ~/Desktop
git clone https://github.com/your-username/AWS_Bedrock_RAG.git
cd AWS_Bedrock_RAG/RAG_Project_AWS_Bedrock
```

### Step 2.2: Add GitHub Secrets

1. **Go to GitHub Repository**
   - Navigate to your repository on GitHub
   - Click **Settings** tab

2. **Navigate to Secrets**
   - Left sidebar → **Secrets and variables** → **Actions**

3. **Add Each Secret** (Click "New repository secret" for each)

   **Secret 1: AWS_ACCESS_KEY_ID**
   ```
   Name: AWS_ACCESS_KEY_ID
   Value: AKIA... (paste your access key)
   ```
   Click "Add secret"

   **Secret 2: AWS_SECRET_ACCESS_KEY**
   ```
   Name: AWS_SECRET_ACCESS_KEY
   Value: (paste your secret key)
   ```
   Click "Add secret"

   **Secret 3: AWS_REGION**
   ```
   Name: AWS_REGION
   Value: us-east-1
   ```
   Click "Add secret"

   **Secret 4: ECR_REGISTRY**
   ```
   Name: ECR_REGISTRY
   Value: 020866158197.dkr.ecr.us-east-1.amazonaws.com
   ```
   (Replace with your actual registry URL)
   Click "Add secret"

   **Secret 5: ECR_REPOSITORY**
   ```
   Name: ECR_REPOSITORY
   Value: flask-app
   ```
   Click "Add secret"

   **Secret 6: EKS_CLUSTER_NAME**
   ```
   Name: EKS_CLUSTER_NAME
   Value: rag-app-cluster
   ```
   Click "Add secret"

4. **Verify All Secrets Added**
   You should see 6 secrets listed:
   - ✅ AWS_ACCESS_KEY_ID
   - ✅ AWS_SECRET_ACCESS_KEY
   - ✅ AWS_REGION
   - ✅ ECR_REGISTRY
   - ✅ ECR_REPOSITORY
   - ✅ EKS_CLUSTER_NAME

---

## 🐳 PHASE 3: Local Testing (Optional but Recommended)

### Step 3.1: Test Docker Build Locally

```bash
# Navigate to project directory
cd RAG_Project_AWS_Bedrock

# Build Docker image
docker build -t rag-app:test .

# Run container locally
docker run -p 8501:8501 \
    -e AWS_ACCESS_KEY_ID=your-key \
    -e AWS_SECRET_ACCESS_KEY=your-secret \
    -e AWS_DEFAULT_REGION=us-east-1 \
    rag-app:test

# Open browser to http://localhost:8501
# Test the application
# Press Ctrl+C to stop
```

### Step 3.2: Push Test Image to ECR (Optional)

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    020866158197.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag rag-app:test \
    020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app:test

# Push image
docker push \
    020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app:test

# Verify image in ECR
aws ecr describe-images \
    --repository-name flask-app \
    --region us-east-1
```

---

## 🚢 PHASE 4: Manual Kubernetes Deployment

### Step 4.1: Create Kubernetes Secret

```bash
# Create AWS credentials secret in Kubernetes
kubectl create secret generic aws-credentials \
    --from-literal=AWS_ACCESS_KEY_ID=your-access-key \
    --from-literal=AWS_SECRET_ACCESS_KEY=your-secret-key

# Verify secret
kubectl get secrets
kubectl describe secret aws-credentials
```

### Step 4.2: Deploy Application

```bash
# Apply deployment
kubectl apply -f deployment.yaml

# Expected output:
# deployment.apps/rag-app created
# service/rag-app-service created
```

### Step 4.3: Monitor Deployment

```bash
# Watch deployment progress
kubectl get deployments --watch

# Check pods (wait for all to be Running)
kubectl get pods

# Check pod details
kubectl describe pods

# View pod logs
kubectl logs -l app=rag-app --tail=50
```

**Wait until you see:**
```
NAME                       READY   STATUS    RESTARTS   AGE
rag-app-7d8f9c5b6d-abc12   1/1     Running   0          2m
rag-app-7d8f9c5b6d-def34   1/1     Running   0          2m
rag-app-7d8f9c5b6d-ghi56   1/1     Running   0          2m
```

### Step 4.4: Get Application URL

```bash
# Check service status
kubectl get services

# Wait for EXTERNAL-IP (may take 2-5 minutes)
kubectl get service rag-app-service --watch
```

**Expected Output:**
```
NAME              TYPE           CLUSTER-IP      EXTERNAL-IP                                                              PORT(S)        AGE
rag-app-service   LoadBalancer   10.100.123.45   a1b2c3d4e5f6-123456789.us-east-1.elb.amazonaws.com   80:31234/TCP   3m
```

### Step 4.5: Access Application

```bash
# Get the external URL
EXTERNAL_IP=$(kubectl get service rag-app-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Application URL: http://$EXTERNAL_IP"

# Open in browser
# Windows:
start http://$EXTERNAL_IP

# Mac:
open http://$EXTERNAL_IP

# Linux:
xdg-open http://$EXTERNAL_IP
```

---

## 🔄 PHASE 5: Automated CI/CD Deployment

### Step 5.1: Commit and Push Changes

```bash
# Check current status
git status

# Add all changes
git add .

# Commit changes
git commit -m "feat: setup complete CI/CD pipeline with Kubernetes deployment"

# Push to main branch (this triggers the pipeline)
git push origin main
```

### Step 5.2: Monitor GitHub Actions

1. **Go to GitHub Repository**
2. **Click "Actions" tab**
3. **You'll see the workflow running**

**Workflow Progress:**
```
✅ Continuous Integration (2-3 minutes)
   ├─ Checkout code
   ├─ Setup Python
   ├─ Install dependencies
   └─ Run tests

✅ Continuous Deployment (3-5 minutes)
   ├─ Configure AWS
   ├─ Login to ECR
   ├─ Build Docker image
   ├─ Tag image
   └─ Push to ECR

✅ Kubernetes Deployment (2-3 minutes)
   ├─ Configure kubectl
   ├─ Create secrets
   ├─ Update deployment
   ├─ Wait for rollout
   └─ Get service URL
```

### Step 5.3: View Deployment Logs

Click on the running workflow to see detailed logs:

1. **Click on the workflow run**
2. **Click on each job to expand**
3. **Click on each step to see logs**

### Step 5.4: Get Application URL from Logs

In the "Kubernetes Deployment" job, look for:
```
🚀 Deployment completed successfully!
📦 Image: 020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app:abc123
🌐 Application URL: http://a1b2c3d4e5f6.us-east-1.elb.amazonaws.com
```

---

## ✅ PHASE 6: Verification

### Step 6.1: Verify Deployment

```bash
# Check all resources
kubectl get all

# Check deployment status
kubectl get deployment rag-app -o wide

# Check pod status
kubectl get pods -l app=rag-app

# Check service
kubectl get service rag-app-service
```

### Step 6.2: Test Application

1. **Open the application URL in browser**
2. **Test Standard RAG:**
   - Enter a question
   - Verify response

3. **Test Corrective RAG:**
   - Select "Corrective RAG (CRAG)" mode
   - Adjust relevance threshold
   - Enter a question
   - Check metadata display

### Step 6.3: Check Logs

```bash
# View application logs
kubectl logs -l app=rag-app --tail=100

# Follow logs in real-time
kubectl logs -l app=rag-app -f

# Check specific pod logs
kubectl logs rag-app-<pod-id>
```

---

## 🔧 PHASE 7: Making Updates

### Step 7.1: Update Code

```bash
# Make changes to your code
# For example, edit rag_app.py

# Test locally first
docker build -t rag-app:test .
docker run -p 8501:8501 rag-app:test
```

### Step 7.2: Deploy Updates

```bash
# Commit changes
git add .
git commit -m "feat: update application feature"

# Push to trigger CI/CD
git push origin main

# The pipeline will automatically:
# 1. Build new Docker image
# 2. Push to ECR
# 3. Update Kubernetes deployment
# 4. Perform rolling update (zero downtime)
```

### Step 7.3: Monitor Rolling Update

```bash
# Watch rollout status
kubectl rollout status deployment/rag-app

# Check rollout history
kubectl rollout history deployment/rag-app

# If needed, rollback
kubectl rollout undo deployment/rag-app
```

---

## 📊 PHASE 8: Monitoring and Maintenance

### Step 8.1: Check Resource Usage

```bash
# Check pod resource usage
kubectl top pods

# Check node resource usage
kubectl top nodes

# Get detailed pod info
kubectl describe pod rag-app-<pod-id>
```

### Step 8.2: Scale Application

```bash
# Scale up to 5 replicas
kubectl scale deployment rag-app --replicas=5

# Scale down to 2 replicas
kubectl scale deployment rag-app --replicas=2

# Verify scaling
kubectl get pods -l app=rag-app
```

### Step 8.3: View Events

```bash
# View recent events
kubectl get events --sort-by=.metadata.creationTimestamp

# Watch events in real-time
kubectl get events --watch
```

---

## 🧹 PHASE 9: Cleanup (When Done)

### Step 9.1: Delete Kubernetes Resources

```bash
# Delete deployment and service
kubectl delete -f deployment.yaml

# Delete secret
kubectl delete secret aws-credentials

# Verify deletion
kubectl get all
```

### Step 9.2: Delete EKS Cluster

```bash
# Using eksctl
eksctl delete cluster --name rag-app-cluster --region us-east-1

# Or using AWS Console
# Go to EKS → Clusters → Select cluster → Delete
```

### Step 9.3: Delete ECR Repository

```bash
# Delete ECR repository
aws ecr delete-repository \
    --repository-name flask-app \
    --region us-east-1 \
    --force
```

---

## 🆘 Troubleshooting Guide

### Issue 1: Pods Not Starting

```bash
# Check pod status
kubectl get pods

# Describe pod for details
kubectl describe pod rag-app-<pod-id>

# Check logs
kubectl logs rag-app-<pod-id>

# Common causes:
# - Image pull errors → Check ECR permissions
# - Crash loop → Check application logs
# - Resource limits → Check node capacity
```

### Issue 2: Service No External IP

```bash
# Check service
kubectl describe service rag-app-service

# Wait longer (can take 5 minutes)
kubectl get service rag-app-service --watch

# Check LoadBalancer events
kubectl get events | grep LoadBalancer
```

### Issue 3: GitHub Actions Failing

1. **Check workflow logs in GitHub Actions tab**
2. **Verify all secrets are set correctly**
3. **Check IAM permissions**
4. **Verify EKS cluster is running**

### Issue 4: Application Errors

```bash
# Check application logs
kubectl logs -l app=rag-app --tail=100

# Check AWS credentials
kubectl get secret aws-credentials -o yaml

# Test AWS access from pod
kubectl exec -it rag-app-<pod-id> -- env | grep AWS
```

---

## 📝 Quick Reference Commands

```bash
# Deployment
kubectl apply -f deployment.yaml
kubectl get deployments
kubectl describe deployment rag-app

# Pods
kubectl get pods
kubectl logs <pod-name>
kubectl exec -it <pod-name> -- /bin/bash

# Services
kubectl get services
kubectl describe service rag-app-service

# Scaling
kubectl scale deployment rag-app --replicas=5

# Updates
kubectl set image deployment/rag-app rag-app=<new-image>
kubectl rollout status deployment/rag-app
kubectl rollout undo deployment/rag-app

# Cleanup
kubectl delete -f deployment.yaml
kubectl delete secret aws-credentials
```

---

## 🎯 Success Checklist

- [ ] ECR repository created
- [ ] EKS cluster running
- [ ] kubectl configured
- [ ] GitHub secrets added
- [ ] Docker image built and pushed
- [ ] Kubernetes secret created
- [ ] Deployment applied successfully
- [ ] All pods running (3/3)
- [ ] Service has external IP
- [ ] Application accessible via browser
- [ ] CI/CD pipeline working
- [ ] Application responding to queries

---

## 📚 Additional Resources

- **AWS EKS Documentation:** https://docs.aws.amazon.com/eks/
- **Kubernetes Documentation:** https://kubernetes.io/docs/
- **GitHub Actions Documentation:** https://docs.github.com/actions
- **AWS Bedrock Documentation:** https://docs.aws.amazon.com/bedrock/

---

## 🎉 Congratulations!

You've successfully deployed your RAG application with:
- ✅ Automated CI/CD pipeline
- ✅ Kubernetes orchestration
- ✅ Auto-scaling capabilities
- ✅ Zero-downtime deployments
- ✅ Production-ready infrastructure

**Your application is now live and accessible!** 🚀