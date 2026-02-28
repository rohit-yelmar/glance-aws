# Glance Backend - Setup & Deployment Guide

Complete guide for setting up and deploying the Glance visual semantic search backend on AWS.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [AWS Account Setup](#2-aws-account-setup)
3. [Environment Variables](#3-environment-variables)
4. [AWS Service Configuration](#4-aws-service-configuration)
5. [Local Development Setup](#5-local-development-setup)
6. [EC2 Deployment](#6-ec2-deployment)
7. [Post-Deployment Verification](#7-post-deployment-verification)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

### Required Accounts

- [AWS Account](https://aws.amazon.com/free/) with console access
- SSH key pair for EC2 access

### Required Tools (Local Machine)

```bash
# macOS (using Homebrew)
brew install awscli python@3.11 git

# Ubuntu/Debian
sudo apt update && sudo apt install -y awscli python3.11 python3.11-venv git

# Verify installations
aws --version        # AWS CLI 2.x recommended
python3 --version    # Python 3.11+
git --version
```

### AWS CLI Configuration

```bash
# Configure AWS CLI with your credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: us-east-1 (or your preferred region)
# Default output format: json
```

**Getting AWS Credentials:**

1. Log into [AWS Console](https://console.aws.amazon.com/)
2. Navigate to IAM → Users → [Your User] → Security credentials
3. Create access key → Download CSV

---

## 2. AWS Account Setup

### 2.1 Request Bedrock Model Access

Amazon Bedrock requires explicit model access approval.

**Steps:**

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click "Model access" in left sidebar
3. Click "Manage model access"
4. Enable these models:
   - **Amazon Nova Lite** (for image analysis)
   - **Amazon Nova Multimodal Embeddings** (for embeddings)
5. Submit request (usually approved within minutes)

**Verification:**

```bash
aws bedrock list-foundation-models --region us-east-1
```

---

## 3. Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

### 3.1 Complete Environment Variables Reference

```bash
# ============================================
# APPLICATION CONFIGURATION
# ============================================
# Environment: development, staging, production
ENVIRONMENT=production

# Application debug mode (true/false)
DEBUG=false

# API port (default: 8000)
PORT=8000

# API Key for authentication (generate a secure random string)
API_KEY=your-secure-api-key-here

# ============================================
# AWS CONFIGURATION
# ============================================
# AWS Region (must match your RDS/OpenSearch region)
AWS_REGION=us-east-1

# AWS Access Keys (optional if using IAM role on EC2)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# ============================================
# BEDROCK MODEL CONFIGURATION
# ============================================
# Amazon Nova 2 Lite model ID
BEDROCK_NOVA_LITE_MODEL_ID=amazon.nova-lite-v1:0

# Amazon Nova Multimodal Embeddings model ID
BEDROCK_EMBEDDING_MODEL_ID=amazon.nova-embeddings-v1:0

# Embedding dimensions (Nova = 1024)
EMBEDDING_DIMENSIONS=1024

# ============================================
# RDS POSTGRESQL CONFIGURATION
# ============================================
# Database host (RDS endpoint)
DB_HOST=glance-db.XXXXXXXX.us-east-1.rds.amazonaws.com

# Database port
DB_PORT=5432

# Database name
DB_NAME=glance_db

# Database user
DB_USER=glance_admin

# Database password (generate strong password)
DB_PASSWORD=your-secure-db-password

# Database connection pool size
DB_POOL_SIZE=10

# ============================================
# OPENSEARCH CONFIGURATION
# ============================================
# OpenSearch domain endpoint (without https://)
OPENSEARCH_HOST=search-glance-XXXXXXXX.us-east-1.es.amazonaws.com

# OpenSearch port
OPENSEARCH_PORT=443

# Use HTTPS (true for AWS OpenSearch)
OPENSEARCH_USE_SSL=true

# Verify SSL certificates
OPENSEARCH_VERIFY_CERTS=true

# OpenSearch index name
OPENSEARCH_INDEX=product_embeddings

# AWS Region for OpenSearch signing
OPENSEARCH_AWS_REGION=us-east-1

# ============================================
# APPLICATION SETTINGS
# ============================================
# Maximum image size in bytes (10MB)
MAX_IMAGE_SIZE=10485760

# Image download timeout in seconds
IMAGE_DOWNLOAD_TIMEOUT=30

# Number of search results from each modality (text/image)
SEARCH_TOP_K=10

# Final number of results to return
SEARCH_FINAL_LIMIT=3

# RRF constant (k value)
RRF_K=60

# ============================================
# LOGGING
# ============================================
# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Enable structured JSON logging
JSON_LOGGING=true
```

### 3.2 Generating Secure Keys

```bash
# Generate secure API key
openssl rand -base64 32

# Generate secure DB password
openssl rand -base64 24
```

---

## 4. AWS Service Configuration

### 4.1 Create RDS PostgreSQL Instance

**Via AWS Console:**

1. Go to [RDS Console](https://console.aws.amazon.com/rds/)
2. Click "Create database"
3. Configuration:
   - **Engine**: PostgreSQL 15.x
   - **Template**: Free tier (or Production)
   - **DB instance identifier**: `glance-db`
   - **Master username**: `glance_admin`
   - **Master password**: [Secure password]
   - **Instance class**: db.t3.micro (Free tier) or db.t3.small
   - **Storage**: 20 GB
   - **VPC**: Default VPC
   - **Public access**: Yes (for development) / No (for production with bastion)
   - **VPC security group**: Create new
   - **Database name**: `glance_db`

4. Security Group Rules (Inbound):
   - Type: PostgreSQL
   - Port: 5432
   - Source: Custom (your IP or EC2 security group)

5. Wait for database to be available (~10 minutes)

**Via AWS CLI:**

```bash
# Create security group
aws ec2 create-security-group \
  --group-name glance-rds-sg \
  --description "Security group for Glance RDS"

# Add inbound rule for PostgreSQL
aws ec2 authorize-security-group-ingress \
  --group-name glance-rds-sg \
  --protocol tcp \
  --port 5432 \
  --cidr $(curl -s ifconfig.me)/32

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier glance-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 20 \
  --storage-type gp2 \
  --master-username glance_admin \
  --master-user-password YOUR_SECURE_PASSWORD \
  --db-name glance_db \
  --vpc-security-group-ids $(aws ec2 describe-security-groups --group-names glance-rds-sg --query 'SecurityGroups[0].GroupId' --output text) \
  --publicly-accessible \
  --region us-east-1

# Wait for database to be available
aws rds wait db-instance-available --db-instance-identifier glance-db
```

**Get RDS Endpoint:**

```bash
aws rds describe-db-instances \
  --db-instance-identifier glance-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

---

### 4.2 Create OpenSearch Domain

**Via AWS Console:**

1. Go to [OpenSearch Console](https://console.aws.amazon.com/es/)
2. Click "Create domain"
3. Configuration:
   - **Domain name**: `glance-search`
   - **Deployment type**: Development and testing
   - **Version**: OpenSearch 2.11
   - **Instance type**: t3.small.search
   - **Number of nodes**: 1
   - **Storage**: EBS, 10 GB
   - **Access policy**: Configure domain level access policy

4. Access Policy (Customize):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:root"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:YOUR_ACCOUNT_ID:domain/glance-search/*"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:role/GlanceEC2Role"
      },
      "Action": "es:*",
      "Resource": "arn:aws:es:us-east-1:YOUR_ACCOUNT_ID:domain/glance-search/*"
    }
  ]
}
```

5. Wait for domain to be active (~15 minutes)

**Via AWS CLI:**

```bash
# Create OpenSearch domain (requires IAM role first - see EC2 setup)
aws opensearch create-domain \
  --domain-name glance-search \
  --engine-version OpenSearch_2.11 \
  --cluster-config InstanceType=t3.small.search,InstanceCount=1 \
  --ebs-options EBSEnabled=true,VolumeSize=10,VolumeType=gp2 \
  --access-policies '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"*"},"Action":"es:*","Resource":"arn:aws:es:us-east-1:'$(aws sts get-caller-identity --query Account --output text)':domain/glance-search/*"}]}' \
  --region us-east-1

# Wait for domain to be active
aws opensearch wait domain-available --domain-name glance-search
```

**Get OpenSearch Endpoint:**

```bash
aws opensearch describe-domain \
  --domain-name glance-search \
  --query 'DomainStatus.Endpoint' \
  --output text
```

---

### 4.3 Create IAM Role for EC2

**Via AWS Console:**

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Roles → Create role
3. Trusted entity: AWS Service → EC2
4. Attach policies:
   - `AmazonBedrockFullAccess` (or scoped policy below)
   - `AmazonRDSReadOnlyAccess`
   - `AmazonOpenSearchServiceFullAccess`

**Scoped Policy (More Secure):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-embeddings-v1:0"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["rds:DescribeDBInstances", "rds:DescribeDBClusters"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpGet",
        "es:ESHttpPut",
        "es:ESHttpPost",
        "es:ESHttpDelete"
      ],
      "Resource": "arn:aws:es:us-east-1:*:domain/glance-search/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/glance/*"
    }
  ]
}
```

5. Role name: `GlanceEC2Role`

---

## 5. Local Development Setup

### 5.1 Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd glance-aws

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5.2 Initialize Databases

```bash
# Initialize PostgreSQL tables
python scripts/init_db.py

# Initialize OpenSearch index
python scripts/init_opensearch.py
```

### 5.3 Run Development Server

```bash
# Load environment variables and run
export $(cat .env | xargs)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.4 Test API

```bash
# Health check
curl http://localhost:8000/health

# Test catalog ingestion
curl -X POST http://localhost:8000/ingest-catalog \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "store_id": "test-store",
    "products": [{
      "product_id": "prod-001",
      "name": "Blue Linen Shirt",
      "description": "A comfortable linen shirt",
      "price": 49.99,
      "category": "shirts",
      "tags": ["summer", "casual"],
      "image_url": "https://example.com/image.jpg"
    }]
  }'

# Test search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "summer blue linen shirt",
    "limit": 3
  }'
```

---

## 6. EC2 Deployment

### 6.1 Launch EC2 Instance

**Via AWS Console:**

1. Go to [EC2 Console](https://console.aws.amazon.com/ec2/)
2. Launch instance
3. Configuration:
   - **Name**: `glance-backend`
   - **AMI**: Ubuntu Server 22.04 LTS (HVM)
   - **Instance type**: t3.medium (2 vCPU, 4GB RAM)
   - **Key pair**: Create or select existing
   - **Network**: Default VPC
   - **Security group**: Create new

4. Security Group Rules:
   | Type | Protocol | Port | Source |
   |------|----------|------|--------|
   | SSH | TCP | 22 | Your IP |
   | HTTP | TCP | 80 | 0.0.0.0/0 |
   | HTTPS | TCP | 443 | 0.0.0.0/0 |
   | Custom TCP | TCP | 8000 | 0.0.0.0/0 (temporary) |

5. Advanced details:
   - **IAM instance profile**: GlanceEC2Role
   - **User data**: (See below)

6. Storage: 20 GB gp3

**Via AWS CLI:**

```bash
# Create security group
aws ec2 create-security-group \
  --group-name glance-ec2-sg \
  --description "Security group for Glance EC2"

# Add rules
aws ec2 authorize-security-group-ingress \
  --group-name glance-ec2-sg \
  --protocol tcp --port 22 --cidr $(curl -s ifconfig.me)/32

aws ec2 authorize-security-group-ingress \
  --group-name glance-ec2-sg \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name glance-ec2-sg \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids $(aws ec2 describe-security-groups --group-names glance-ec2-sg --query 'SecurityGroups[0].GroupId' --output text) \
  --iam-instance-profile Name=GlanceEC2Role \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=glance-backend}]'
```

### 6.2 EC2 Setup Script

Create `scripts/setup_ec2.sh`:

```bash
#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential libpq-dev

# Install nginx
sudo apt install -y nginx

# # Install CloudWatch agent (optional but recommended)
# wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
# sudo dpkg -i amazon-cloudwatch-agent.deb

# Create app directory
sudo mkdir -p /opt/glance
sudo chown ubuntu:ubuntu /opt/glance

# Clone repository
cd /opt/glance
git clone <your-repo-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file (you'll need to edit this manually or use SSM Parameter Store)
cp .env.example .env
# IMPORTANT: Edit .env with your actual values

# Initialize databases
python scripts/init_db.py
python scripts/init_opensearch.py

# Create systemd service
sudo tee /etc/systemd/system/glance.service > /dev/null <<EOF
[Unit]
Description=Glance FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/glance
Environment=PATH=/opt/glance/venv/bin
EnvironmentFile=/opt/glance/.env
ExecStart=/opt/glance/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
sudo tee /etc/nginx/sites-available/glance > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable nginx config
sudo ln -sf /etc/nginx/sites-available/glance /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Start services
sudo systemctl daemon-reload
sudo systemctl enable glance
sudo systemctl start glance
sudo systemctl restart nginx

echo "Setup complete! Check status with: sudo systemctl status glance"
```

Run on EC2:

```bash
# Copy setup script to EC2
scp -i your-key.pem scripts/setup_ec2.sh ubuntu@YOUR_EC2_IP:/home/ubuntu/

# SSH into EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Run setup
chmod +x setup_ec2.sh
./setup_ec2.sh
```

### 6.3 Configure Environment on EC2

Edit the `.env` file with your actual values:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
sudo nano /opt/glance/.env
```

Update all placeholder values, then restart:

```bash
sudo systemctl restart glance
```

---

## 7. Post-Deployment Verification

### 7.1 Check Service Status

```bash
# Check application status
sudo systemctl status glance

# View logs
sudo journalctl -u glance -f

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 7.2 API Health Check

```bash
# Replace with your EC2 public IP or domain
curl http://YOUR_EC2_IP/health

# Expected response:
# {"status": "healthy", "services": {...}, "version": "1.0.0"}
```

### 7.3 End-to-End Test

```bash
# Test catalog ingestion
curl -X POST http://YOUR_EC2_IP/ingest-catalog \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "store_id": "demo-store",
    "products": [{
      "product_id": "shirt-001",
      "name": "Classic Blue Linen Shirt",
      "description": "Breathable linen shirt perfect for summer",
      "price": 59.99,
      "category": "shirts",
      "tags": ["linen", "blue", "summer", "casual"],
      "image_url": "https://your-s3-bucket.s3.amazonaws.com/shirt-001.jpg"
    }]
  }'

# Wait a few minutes for processing, then search
curl -X POST http://YOUR_EC2_IP/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "summer solid light blue linen shirt",
    "limit": 3
  }'
```

---

## 8. Troubleshooting

### 8.1 Common Issues

**Issue**: Bedrock access denied

```
Error: An error occurred (AccessDeniedException) when calling InvokeModel
```

**Solution**:

- Verify Bedrock model access is granted in console
- Check IAM role has `bedrock:InvokeModel` permission
- Ensure correct region in AWS_REGION env var

**Issue**: OpenSearch connection timeout

```
ConnectionTimeout: Connection timed out
```

**Solution**:

- Verify OpenSearch domain is in `Active` state
- Check security group allows port 443 from EC2
- Verify IAM role has OpenSearch permissions

**Issue**: RDS connection refused

```
Connection refused: PostgreSQL server
```

**Solution**:

- Check RDS security group allows port 5432 from EC2
- Verify DB instance is `Available` in console
- Check credentials in .env file

**Issue**: Application won't start

```bash
# Check logs
sudo journalctl -u glance -n 100

# Check environment variables
sudo systemctl show glance --property=Environment

# Manual test
sudo su - ubuntu
cd /opt/glance
source venv/bin/activate
export $(cat .env | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8.2 Performance Tuning

**High Memory Usage:**

- Reduce DB_POOL_SIZE in .env
- Add swap space: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

**Slow Search Queries:**

- Increase OpenSearch instance size
- Tune ef_search parameter (lower = faster, less accurate)
- Enable OpenSearch caching

**Slow Catalog Processing:**

- Use larger EC2 instance (t3.large)
- Process in smaller batches
- Add retry logic with exponential backoff

### 8.3 Security Checklist

- [ ] RDS password is strong and unique
- [ ] API_KEY is cryptographically secure
- [ ] Security groups restrict access appropriately
- [ ] IAM role has minimal required permissions
- [ ] No hardcoded credentials in code
- [ ] .env file has restricted permissions: `chmod 600 .env`
- [ ] Nginx configured to hide server tokens
- [ ] HTTPS enabled (using ACM + ALB, or Let's Encrypt)

### 8.4 Setting Up HTTPS (Production)

**Option A: Application Load Balancer (Recommended)**

1. Request certificate in [AWS ACM](https://console.aws.amazon.com/acm/)
2. Create Application Load Balancer
3. Configure HTTPS listener with ACM certificate
4. Target group points to EC2 instance on port 80
5. Update security group to allow only ALB access

**Option B: Let's Encrypt (Direct on EC2)**

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Quick Reference Commands

```bash
# Restart application
sudo systemctl restart glance

# View logs
sudo journalctl -u glance -f

# Check nginx
sudo nginx -t && sudo systemctl restart nginx

# Database connection test
psql -h YOUR_RDS_ENDPOINT -U glance_admin -d glance_db

# OpenSearch test
curl -X GET https://YOUR_OPENSEARCH_ENDPOINT/_cluster/health

# Check AWS credentials on EC2
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

---

**Support**: For issues, check CloudWatch logs and application logs first.  
**Updates**: To update deployment, pull latest code and restart service:

```bash
cd /opt/glance && git pull && sudo systemctl restart glance
```
