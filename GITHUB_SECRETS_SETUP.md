# GitHub Secrets Setup Guide

This guide explains how to configure GitHub Secrets for the CI/CD pipeline.

## Required GitHub Secrets

You need to add the following secrets to your GitHub repository:

### 1. AWS Credentials
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret access key
- `AWS_REGION` - AWS region (e.g., `us-east-1`)

### 2. ECR Configuration
- `ECR_REGISTRY` - Your ECR registry URL (e.g., `020866158197.dkr.ecr.us-east-1.amazonaws.com`)
- `ECR_REPOSITORY` - Your ECR repository name (e.g., `flask-app`)

### 3. EKS Configuration
- `EKS_CLUSTER_NAME` - Your EKS cluster name (e.g., `rag-app-cluster`)

## Step-by-Step Setup

### Step 1: Navigate to GitHub Repository Settings

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click on **Secrets and variables** → **Actions**

### Step 2: Add Each Secret

Click **New repository secret** and add each of the following:

#### AWS_ACCESS_KEY_ID
```
Name: AWS_ACCESS_KEY_ID
Value: AKIA... (your AWS access key)
```

#### AWS_SECRET_ACCESS_KEY
```
Name: AWS_SECRET_ACCESS_KEY
Value: your-secret-access-key
```

#### AWS_REGION
```
Name: AWS_REGION
Value: us-east-1
```

#### ECR_REGISTRY
```
Name: ECR_REGISTRY
Value: 020866158197.dkr.ecr.us-east-1.amazonaws.com
```

#### ECR_REPOSITORY
```
Name: ECR_REPOSITORY
Value: flask-app
```

#### EKS_CLUSTER_NAME
```
Name: EKS_CLUSTER_NAME
Value: your-eks-cluster-name
```

### Step 3: Verify Secrets

After adding all secrets, you should see them listed in the Actions secrets page:
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY
- ✅ AWS_REGION
- ✅ ECR_REGISTRY
- ✅ ECR_REPOSITORY
- ✅ EKS_CLUSTER_NAME

## How to Get These Values

### Getting AWS Credentials

1. **AWS Access Key ID and Secret Access Key:**
   ```bash
   # If you have AWS CLI configured
   cat ~/.aws/credentials
   ```
   
   Or create new credentials:
   - Go to AWS Console → IAM → Users
   - Select your user → Security credentials
   - Click "Create access key"
   - Download and save the credentials

2. **AWS Region:**
   - Check your AWS Console URL or
   - Run: `aws configure get region`

### Getting ECR Registry URL

```bash
# Get ECR registry URL
aws ecr describe-repositories --region us-east-1

# Or construct it manually:
# Format: {account-id}.dkr.ecr.{region}.amazonaws.com
# Example: 020866158197.dkr.ecr.us-east-1.amazonaws.com
```

### Getting ECR Repository Name

```bash
# List ECR repositories
aws ecr describe-repositories --region us-east-1 --query 'repositories[*].repositoryName'

# Your repository name (e.g., flask-app)
```

### Getting EKS Cluster Name

```bash
# List EKS clusters
aws eks list-clusters --region us-east-1

# Get cluster details
aws eks describe-cluster --name your-cluster-name --region us-east-1
```

## IAM Permissions Required

Your AWS user/role needs the following permissions:

### ECR Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

### EKS Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    }
  ]
}
```

### Kubernetes RBAC

Your AWS user also needs Kubernetes RBAC permissions. Add to your EKS cluster:

```bash
# Edit aws-auth ConfigMap
kubectl edit configmap aws-auth -n kube-system
```

Add your IAM user/role to the mapUsers section:
```yaml
mapUsers: |
  - userarn: arn:aws:iam::020866158197:user/your-username
    username: your-username
    groups:
      - system:masters
```

## Testing the Setup

### Test 1: Verify Secrets in Workflow

The workflow includes a debug step that will show (masked) secret names:
```yaml
- name: Debug Secrets
  run: |
    echo "REGISTRY=${{ secrets.ECR_REGISTRY }}"
    echo "REPOSITORY=${{ secrets.ECR_REPOSITORY }}"
    echo "REGION=${{ secrets.AWS_REGION }}"
```

### Test 2: Manual Workflow Run

1. Go to **Actions** tab in GitHub
2. Select **CI-CD-Pipeline** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

### Test 3: Push to Main Branch

```bash
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add .
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

## Troubleshooting

### Issue: "Secret not found"
**Solution:** Double-check secret names match exactly (case-sensitive)

### Issue: "AWS authentication failed"
**Solution:** 
- Verify AWS credentials are correct
- Check IAM user has required permissions
- Ensure credentials haven't expired

### Issue: "ECR authentication failed"
**Solution:**
- Verify ECR_REGISTRY format is correct
- Check ECR repository exists
- Ensure IAM user has ECR permissions

### Issue: "EKS cluster not found"
**Solution:**
- Verify EKS_CLUSTER_NAME is correct
- Check cluster exists in the specified region
- Ensure IAM user has EKS describe permissions

### Issue: "kubectl: command not found"
**Solution:** The workflow installs kubectl automatically, but if it fails:
- Check the workflow logs
- Verify the azure/setup-kubectl action is working

## Security Best Practices

1. **Rotate Credentials Regularly**
   - Update AWS access keys every 90 days
   - Update GitHub secrets when credentials change

2. **Use Least Privilege**
   - Grant only necessary IAM permissions
   - Use separate IAM users for CI/CD

3. **Monitor Access**
   - Enable CloudTrail logging
   - Review GitHub Actions logs regularly

4. **Protect Secrets**
   - Never commit secrets to repository
   - Use GitHub's secret scanning
   - Enable branch protection rules

## CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Push to main branch                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Continuous Integration                                   │
│    - Checkout code                                          │
│    - Setup Python                                           │
│    - Install dependencies                                   │
│    - Run tests                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Continuous Deployment                                    │
│    - Configure AWS credentials                              │
│    - Login to ECR                                           │
│    - Build Docker image                                     │
│    - Tag image (latest + commit SHA)                        │
│    - Push to ECR                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Kubernetes Deployment                                    │
│    - Configure AWS credentials                              │
│    - Install kubectl                                        │
│    - Update kubeconfig for EKS                              │
│    - Create/update AWS credentials secret                   │
│    - Update deployment image                                │
│    - Apply deployment                                       │
│    - Wait for rollout                                       │
│    - Get service URL                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Application Running                                      │
│    - Access via LoadBalancer URL                            │
│    - 3 replicas running                                     │
│    - Auto-scaling enabled                                   │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

After setting up secrets:

1. ✅ Verify all secrets are added
2. ✅ Check IAM permissions
3. ✅ Test with a manual workflow run
4. ✅ Push code to trigger automatic deployment
5. ✅ Monitor workflow execution in Actions tab
6. ✅ Access deployed application via LoadBalancer URL

## Support

If you encounter issues:
1. Check GitHub Actions logs
2. Verify all secrets are correctly set
3. Review IAM permissions
4. Check EKS cluster status
5. Verify ECR repository exists