# CI/CD Pipeline Troubleshooting Guide

## Common Errors and Solutions

### Error 1: EKS_CLUSTER_NAME is Empty

**Error Message:**
```
Error: aws: [ERROR]: An error occurred (ParamValidation): argument --name: expected one argument
```

**Cause:** The `EKS_CLUSTER_NAME` GitHub secret is not set or is empty.

**Solution:**

1. **Check if EKS cluster exists:**
   ```bash
   aws eks list-clusters --region us-east-1
   ```

2. **Add the secret to GitHub:**
   - Go to your GitHub repository
   - Click **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `EKS_CLUSTER_NAME`
   - Value: Your cluster name (e.g., `rag-app-cluster`)
   - Click **Add secret**

3. **Verify the secret:**
   - The secret should appear in the list
   - Re-run the workflow

### Error 2: Deployment Not Found

**Error Message:**
```
Error from server (NotFound): deployments.apps "rag-app" not found
```

**Cause:** The workflow tried to update a deployment that doesn't exist yet.

**Solution:** ✅ **FIXED in updated workflow**

The workflow now:
1. Checks if deployment exists
2. Applies deployment.yaml first (creates if not exists)
3. Then updates the image

**Manual Fix (if needed):**
```bash
# Apply deployment first
kubectl apply -f deployment.yaml

# Then the workflow can update it
```

### Error 3: --record Flag Deprecated

**Warning Message:**
```
Flag --record has been deprecated, --record will be removed in the future
```

**Solution:** ✅ **FIXED in updated workflow**

Removed the `--record` flag from the `kubectl set image` command.

---

## Complete Fix Applied

The workflow has been updated with these improvements:

### 1. Proper Deployment Order
```yaml
# OLD (WRONG ORDER):
- Update deployment image  ❌ (fails if deployment doesn't exist)
- Apply deployment

# NEW (CORRECT ORDER):
- Check if deployment exists  ✅
- Apply deployment (creates or updates)  ✅
- Update image to specific SHA  ✅
```

### 2. Better Error Handling
```yaml
- name: Check if deployment exists
  run: |
    if kubectl get deployment rag-app 2>/dev/null; then
      echo "✅ Deployment exists, will update"
    else
      echo "📦 Creating new deployment"
    fi
```

### 3. Removed Deprecated Flags
```yaml
# OLD:
kubectl set image deployment/rag-app ... --record

# NEW:
kubectl set image deployment/rag-app ...
```

---

## Required GitHub Secrets Checklist

Ensure ALL these secrets are set:

- [ ] **AWS_ACCESS_KEY_ID** - Your AWS access key
- [ ] **AWS_SECRET_ACCESS_KEY** - Your AWS secret key
- [ ] **AWS_REGION** - e.g., `us-east-1`
- [ ] **ECR_REGISTRY** - e.g., `020866158197.dkr.ecr.us-east-1.amazonaws.com`
- [ ] **ECR_REPOSITORY** - e.g., `flask-app`
- [ ] **EKS_CLUSTER_NAME** - e.g., `rag-app-cluster` ⚠️ **MOST COMMON ISSUE**

---

## How to Verify Secrets

### Method 1: Check in GitHub UI
1. Go to repository **Settings**
2. **Secrets and variables** → **Actions**
3. You should see all 6 secrets listed

### Method 2: Check Workflow Logs
The workflow includes a debug step that shows (masked) secret values:
```yaml
- name: Debug Secrets
  run: |
    echo "REGISTRY=${{ secrets.ECR_REGISTRY }}"
    echo "REPOSITORY=${{ secrets.ECR_REPOSITORY }}"
    echo "REGION=${{ secrets.AWS_REGION }}"
```

Look for this in the workflow logs. If you see empty values, the secret is not set.

---

## Step-by-Step Fix for Your Current Error

### Step 1: Create EKS Cluster (if not exists)

```bash
# Check if cluster exists
aws eks list-clusters --region us-east-1

# If no cluster, create one
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

### Step 2: Add EKS_CLUSTER_NAME Secret

1. **Get your cluster name:**
   ```bash
   aws eks list-clusters --region us-east-1
   ```
   Output example:
   ```json
   {
       "clusters": [
           "rag-app-cluster"
       ]
   }
   ```

2. **Add to GitHub:**
   - Go to GitHub repository
   - Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `EKS_CLUSTER_NAME`
   - Value: `rag-app-cluster` (your actual cluster name)
   - Add secret

### Step 3: Re-run the Workflow

1. Go to **Actions** tab in GitHub
2. Click on the failed workflow run
3. Click **Re-run all jobs**

OR

```bash
# Make a small change and push
git commit --allow-empty -m "chore: re-trigger workflow"
git push origin main
```

---

## Workflow Execution Order

The updated workflow now executes in this order:

```
1. Continuous Integration
   ├─ Checkout code
   ├─ Setup Python
   ├─ Install dependencies
   └─ Run tests

2. Continuous Deployment
   ├─ Configure AWS
   ├─ Login to ECR
   ├─ Build Docker image
   ├─ Tag image (latest + SHA)
   └─ Push to ECR

3. Kubernetes Deployment
   ├─ Validate secrets (NEW - checks EKS_CLUSTER_NAME)
   ├─ Configure AWS
   ├─ Install kubectl
   ├─ Update kubeconfig
   ├─ Verify connection
   ├─ Create K8s secrets
   ├─ Check if deployment exists (NEW)
   ├─ Apply deployment.yaml (MOVED UP)
   ├─ Update image to SHA (MOVED DOWN)
   ├─ Wait for rollout
   ├─ Verify deployment
   └─ Get service URL
```

---

## Testing the Fix

### Test 1: Validate Secrets Locally

```bash
# Set environment variables (use your actual values)
export EKS_CLUSTER_NAME="rag-app-cluster"
export AWS_REGION="us-east-1"

# Test the command that was failing
aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION

# Should succeed and output:
# Added new context arn:aws:eks:us-east-1:...:cluster/rag-app-cluster to ~/.kube/config
```

### Test 2: Manual Deployment

```bash
# Configure kubectl
aws eks update-kubeconfig --name rag-app-cluster --region us-east-1

# Create secret
kubectl create secret generic aws-credentials \
    --from-literal=AWS_ACCESS_KEY_ID=your-key \
    --from-literal=AWS_SECRET_ACCESS_KEY=your-secret

# Apply deployment
kubectl apply -f deployment.yaml

# Check status
kubectl get deployments
kubectl get pods
kubectl get services
```

### Test 3: Trigger Workflow

```bash
# Push to main branch
git add .
git commit -m "fix: update workflow with proper deployment order"
git push origin main

# Monitor in GitHub Actions tab
```

---

## Quick Reference: All Required Values

| Secret Name | Example Value | How to Get |
|-------------|---------------|------------|
| AWS_ACCESS_KEY_ID | `AKIAIOSFODNN7EXAMPLE` | AWS IAM Console or `aws configure get aws_access_key_id` |
| AWS_SECRET_ACCESS_KEY | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | AWS IAM Console or `aws configure get aws_secret_access_key` |
| AWS_REGION | `us-east-1` | Your AWS region |
| ECR_REGISTRY | `020866158197.dkr.ecr.us-east-1.amazonaws.com` | `aws ecr describe-repositories` |
| ECR_REPOSITORY | `flask-app` | Your ECR repository name |
| EKS_CLUSTER_NAME | `rag-app-cluster` | `aws eks list-clusters` |

---

## Still Having Issues?

### Check Workflow Logs

1. Go to **Actions** tab
2. Click on the failed workflow
3. Click on the failed job
4. Expand each step to see detailed logs
5. Look for the exact error message

### Common Issues

**Issue:** "Could not find credentials"
- **Fix:** Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set

**Issue:** "Cluster not found"
- **Fix:** Verify EKS_CLUSTER_NAME matches your actual cluster name

**Issue:** "Access denied"
- **Fix:** Verify IAM user has EKS and ECR permissions

**Issue:** "Repository not found"
- **Fix:** Verify ECR_REPOSITORY name is correct

---

## Success Indicators

When everything is working correctly, you should see:

✅ All workflow steps green
✅ Docker image pushed to ECR
✅ Deployment created/updated
✅ All pods running (3/3)
✅ Service has external IP
✅ Application accessible via URL

---

## Next Steps After Fix

1. ✅ Verify all secrets are set
2. ✅ Re-run the workflow
3. ✅ Monitor the deployment
4. ✅ Access the application
5. ✅ Test functionality

**The workflow is now fixed and should work correctly!** 🎉