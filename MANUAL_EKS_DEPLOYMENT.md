# Manual EKS Deployment Guide (ECR Already Done)

Since your Docker image is already in ECR, you can deploy directly to Kubernetes.

---

## Prerequisites ✅

- [x] Docker image in ECR
- [ ] EKS cluster running
- [ ] kubectl installed
- [ ] AWS CLI configured

---

## Quick Deployment (5 Steps)

### Step 1: Configure kubectl for EKS

```bash
# Update kubeconfig to connect to your EKS cluster
aws eks update-kubeconfig --name rag-app-cluster --region us-east-1

# Verify connection
kubectl cluster-info
kubectl get nodes
```

**Expected Output:**
```
Kubernetes control plane is running at https://...
CoreDNS is running at https://...

NAME                                          STATUS   ROLES    AGE
ip-192-168-x-x.us-east-1.compute.internal    Ready    <none>   5m
```

### Step 2: Create AWS Credentials Secret

```bash
# Create Kubernetes secret with your AWS credentials
kubectl create secret generic aws-credentials \
    --from-literal=AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY \
    --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY

# Verify secret created
kubectl get secrets
```

**Expected Output:**
```
NAME               TYPE     DATA   AGE
aws-credentials    Opaque   2      5s
```

### Step 3: Deploy Application

```bash
# Navigate to project directory
cd RAG_Project_AWS_Bedrock

# Apply deployment
kubectl apply -f deployment.yaml
```

**Expected Output:**
```
deployment.apps/rag-app created
service/rag-app-service created
```

### Step 4: Monitor Deployment

```bash
# Watch pods starting (wait for all to be Running)
kubectl get pods --watch

# Press Ctrl+C when all pods are Running
```

**Expected Output:**
```
NAME                       READY   STATUS    RESTARTS   AGE
rag-app-7d8f9c5b6d-abc12   1/1     Running   0          2m
rag-app-7d8f9c5b6d-def34   1/1     Running   0          2m
rag-app-7d8f9c5b6d-ghi56   1/1     Running   0          2m
```

### Step 5: Get Application URL

```bash
# Get service details (wait for EXTERNAL-IP)
kubectl get service rag-app-service --watch

# Press Ctrl+C when EXTERNAL-IP appears
```

**Expected Output:**
```
NAME              TYPE           EXTERNAL-IP                                    PORT(S)        AGE
rag-app-service   LoadBalancer   a1b2c3d4.us-east-1.elb.amazonaws.com          80:31234/TCP   3m
```

**Access your application:**
```bash
# Copy the EXTERNAL-IP and open in browser
# Example: http://a1b2c3d4.us-east-1.elb.amazonaws.com
```

---

## Complete Command Sequence (Copy-Paste)

```bash
# 1. Configure kubectl
aws eks update-kubeconfig --name rag-app-cluster --region us-east-1

# 2. Create secret (replace with your actual credentials)
kubectl create secret generic aws-credentials \
    --from-literal=AWS_ACCESS_KEY_ID=AKIA... \
    --from-literal=AWS_SECRET_ACCESS_KEY=your-secret-key

# 3. Deploy
cd RAG_Project_AWS_Bedrock
kubectl apply -f deployment.yaml

# 4. Check status
kubectl get pods
kubectl get services

# 5. Get URL
kubectl get service rag-app-service
```

---

## If You Don't Have EKS Cluster Yet

### Option 1: Create with eksctl (Recommended - 15 minutes)

```bash
# Install eksctl if not installed
# Windows: choco install eksctl
# Mac: brew install eksctl

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

# Wait 15-20 minutes for cluster creation
# kubectl will be automatically configured
```

### Option 2: Create via AWS Console (20 minutes)

1. Go to AWS Console → EKS
2. Click **Create cluster**
3. **Cluster name:** `rag-app-cluster`
4. **Kubernetes version:** 1.28 or latest
5. **VPC:** Use default or create new
6. Click **Create**
7. Wait for cluster to be Active
8. Create Node Group:
   - Name: `standard-workers`
   - Instance type: `t3.medium`
   - Desired size: 3
9. Configure kubectl:
   ```bash
   aws eks update-kubeconfig --name rag-app-cluster --region us-east-1
   ```

---

## Verification Steps

### Check Deployment Status

```bash
# Check all resources
kubectl get all

# Check deployment
kubectl get deployment rag-app

# Check pods
kubectl get pods -l app=rag-app

# Check service
kubectl get service rag-app-service
```

### View Logs

```bash
# View logs from all pods
kubectl logs -l app=rag-app --tail=50

# View logs from specific pod
kubectl logs rag-app-<pod-id>

# Follow logs in real-time
kubectl logs -l app=rag-app -f
```

### Check Pod Details

```bash
# Describe pod for detailed info
kubectl describe pod rag-app-<pod-id>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## Troubleshooting

### Issue: Pods Not Starting

```bash
# Check pod status
kubectl get pods

# Describe pod for details
kubectl describe pod rag-app-<pod-id>

# Check logs
kubectl logs rag-app-<pod-id>
```

**Common causes:**
- ImagePullBackOff → Check ECR image exists and permissions
- CrashLoopBackOff → Check application logs
- Pending → Check node resources

### Issue: No External IP

```bash
# Check service
kubectl describe service rag-app-service

# Wait 2-5 minutes for LoadBalancer provisioning
kubectl get service rag-app-service --watch
```

### Issue: Can't Access Application

```bash
# Check if pods are running
kubectl get pods

# Check service endpoints
kubectl get endpoints rag-app-service

# Check security groups (AWS Console)
# Ensure port 80 is open
```

---

## Scaling

### Scale Up

```bash
# Scale to 5 replicas
kubectl scale deployment rag-app --replicas=5

# Verify
kubectl get pods
```

### Scale Down

```bash
# Scale to 1 replica
kubectl scale deployment rag-app --replicas=1

# Verify
kubectl get pods
```

---

## Updating Application

### Update to New Image

```bash
# If you push a new image to ECR
kubectl set image deployment/rag-app \
    rag-app=020866158197.dkr.ecr.us-east-1.amazonaws.com/flask-app:new-tag

# Watch rollout
kubectl rollout status deployment/rag-app
```

### Restart Deployment

```bash
# Restart all pods (pulls latest image if tag is 'latest')
kubectl rollout restart deployment/rag-app

# Watch status
kubectl rollout status deployment/rag-app
```

---

## Cleanup

### Delete Deployment

```bash
# Delete deployment and service
kubectl delete -f deployment.yaml

# Delete secret
kubectl delete secret aws-credentials

# Verify deletion
kubectl get all
```

### Delete EKS Cluster (When Done)

```bash
# Using eksctl
eksctl delete cluster --name rag-app-cluster --region us-east-1

# Or via AWS Console
# EKS → Clusters → Select cluster → Delete
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `kubectl get pods` | List all pods |
| `kubectl get services` | List all services |
| `kubectl logs <pod-name>` | View pod logs |
| `kubectl describe pod <pod-name>` | Pod details |
| `kubectl delete pod <pod-name>` | Delete pod (will recreate) |
| `kubectl scale deployment rag-app --replicas=N` | Scale deployment |
| `kubectl rollout restart deployment/rag-app` | Restart deployment |
| `kubectl get events` | View cluster events |

---

## Success Checklist

- [ ] kubectl configured for EKS
- [ ] AWS credentials secret created
- [ ] Deployment applied
- [ ] All 3 pods running
- [ ] Service has external IP
- [ ] Application accessible in browser
- [ ] Application responds to queries

---

## Your Current Status

Based on your message:
- ✅ ECR image already pushed
- ⏳ Need to deploy to EKS

**Next Steps:**
1. Ensure EKS cluster exists (or create one)
2. Run the 5-step deployment above
3. Access your application!

**Estimated Time:** 5 minutes (if cluster exists) or 20 minutes (if creating cluster)

---

## Need Help?

If you encounter issues:
1. Check pod logs: `kubectl logs -l app=rag-app`
2. Check pod status: `kubectl describe pods`
3. Check service: `kubectl describe service rag-app-service`
4. See TROUBLESHOOTING_CICD.md for more details

**You're almost there!** 🚀