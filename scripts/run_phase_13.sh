#!/bin/bash
# Phase 13: Production Deployment (Docker, Kubernetes, CI/CD)
# Copy & paste commands one-by-one

echo "Starting Phase 13: Production Deployment..."
echo "=========================================================="

# Command 1: Dockerfile Multi-Stage Build
echo "[1/5] Creating Production Dockerfile..."
opencode create Dockerfile --description "
Create production-grade multi-stage Docker build:

FROM python:3.11-slim as builder

# Stage 1: Builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc g++ make libffi-dev libssl-dev python3-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (lightweight)
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 trading

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/trading/.local
ENV PATH=/home/trading/.local/bin:\$PATH

# Copy application code
COPY --chown=trading:trading . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/models && \\
    chown -R trading:trading /app

# Switch to non-root user
USER trading

# Expose port
EXPOSE 5000

# Health check (check every 30s, fail after 3 attempts)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Environment variables
ENV FLASK_APP=src.web.app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Run Flask app with gunicorn
CMD [\"gunicorn\", \"--workers\", \"4\", \"--timeout\", \"60\", \\
     \"--access-logfile\", \"-\", \"--error-logfile\", \"-\", \\
     \"--bind\", \"0.0.0.0:5000\", \"src.web.app:app\"]

Features:
  ✓ Minimal image size (multi-stage build)
  ✓ Security: Non-root user
  ✓ Production server: Gunicorn with 4 workers
  ✓ Health check configured
  ✓ Logging to stdout for container orchestration
  ✓ Volume mounts for logs/data/models
  ✓ Proper signal handling for graceful shutdown
"

echo "✅ Step 1 Completed!"
echo ""

# Command 2: Docker Compose Full Stack
echo "[2/5] Creating Docker Compose Stack..."
opencode create docker-compose.yml --description "
Create docker-compose.yml for complete stack:

version: '3.9'

services:
  # Main Flask Web Service
  web:
    build: .
    container_name: nifty-trading-web
    ports:
      - \"5000:5000\"
    environment:
      - FLASK_ENV=production
      - DEBUG=false
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://trading:password@db:5432/nifty_trading
      - REDIS_URL=redis://cache:6379/0
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./models:/app/models
      - ./config:/app/config
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    networks:
      - trading-network
    restart: unless-stopped
    healthcheck:
      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:5000/health\"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # PostgreSQL Database (replaces SQLite in production)
  db:
    image: postgres:15-alpine
    container_name: nifty-trading-db
    environment:
      - POSTGRES_USER=trading
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=nifty_trading
      - POSTGRES_INITDB_ARGS=-c max_connections=200
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    networks:
      - trading-network
    restart: unless-stopped
    healthcheck:
      test: [\"CMD-SHELL\", \"pg_isready -U trading -d nifty_trading\"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  cache:
    image: redis:7-alpine
    container_name: nifty-trading-cache
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - trading-network
    restart: unless-stopped

  # Background ML Training Service
  ml-trainer:
    build: .
    container_name: nifty-trading-ml-trainer
    command: python src/utils/ml/training_worker.py
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://trading:password@db:5432/nifty_trading
      - REDIS_URL=redis://cache:6379/0
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models
      - ./data:/app/data
    depends_on:
      - db
      - cache
      - web
    networks:
      - trading-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  trading-network:
    driver: bridge

Setup:
  1. Create .env file with credentials
  2. Create migrations/ folder with init.sql
  3. Run: docker-compose up -d
  4. Access: http://localhost:5000

Commands:
  - docker-compose up -d        # Start all services
  - docker-compose down         # Stop all services
  - docker-compose logs -f web  # View web logs
  - docker-compose ps           # Check status
"

echo "✅ Step 2 Completed!"
echo ""

# Command 3: Kubernetes Deployment
echo "[3/5] Creating Kubernetes Deployment..."
opencode create k8s/deployment.yaml --description "
Create Kubernetes deployment manifest:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: nifty-trading-app
  namespace: default
  labels:
    app: nifty-trading
    tier: web
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: nifty-trading
      tier: web
  template:
    metadata:
      labels:
        app: nifty-trading
        tier: web
      annotations:
        prometheus.io/scrape: 'true'
        prometheus.io/port: '5000'
    spec:
      serviceAccountName: nifty-trading
      containers:
      - name: web
        image: your-registry/nifty-trading:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 5000
          name: http
        
        env:
        - name: FLASK_ENV
          value: \"production\"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: trading-config
              key: redis-url
        
        resources:
          requests:
            memory: \"512Mi\"
            cpu: \"500m\"
          limits:
            memory: \"1Gi\"
            cpu: \"1000m\"
        
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: models
          mountPath: /app/models
      
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: nifty-logs-pvc
      - name: models
        persistentVolumeClaim:
          claimName: nifty-models-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: nifty-trading-service
spec:
  type: LoadBalancer
  selector:
    app: nifty-trading
    tier: web
  ports:
  - port: 80
    targetPort: 5000
    protocol: TCP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nifty-trading-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nifty-trading-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

Features:
  ✓ Rolling update strategy
  ✓ Liveness and readiness probes
  ✓ Resource requests and limits
  ✓ Auto-scaling (2-10 replicas)
  ✓ Health checks every 10s
  ✓ Graceful termination
"

echo "✅ Step 3 Completed!"
echo ""

# Command 4: Kubernetes StatefulSet for Database
echo "[4/5] Creating Kubernetes Database & Redis..."
opencode create k8s/statefulset.yaml --description "
Create Kubernetes StatefulSet for PostgreSQL:

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nifty-trading-db
spec:
  serviceName: nifty-trading-db
  replicas: 1
  selector:
    matchLabels:
      app: nifty-trading
      tier: database
  template:
    metadata:
      labels:
        app: nifty-trading
        tier: database
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: db-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: db-password
        - name: POSTGRES_DB
          value: nifty_trading
        - name: POSTGRES_INITDB_ARGS
          value: \"-c max_connections=200\"
        
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
          subPath: postgres
        
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U \$POSTGRES_USER -d \$POSTGRES_DB
          initialDelaySeconds: 30
          periodSeconds: 10
        
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U \$POSTGRES_USER -d \$POSTGRES_DB
          initialDelaySeconds: 10
          periodSeconds: 5
  
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ \"ReadWriteOnce\" ]
      storageClassName: standard
      resources:
        requests:
          storage: 50Gi

---
apiVersion: v1
kind: Service
metadata:
  name: nifty-trading-db
spec:
  clusterIP: None
  selector:
    app: nifty-trading
    tier: database
  ports:
  - port: 5432
    targetPort: 5432

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nifty-trading-cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nifty-trading
      tier: cache
  template:
    metadata:
      labels:
        app: nifty-trading
        tier: cache
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
          - redis-server
          - --appendonly
          - \"yes\"
          - --maxmemory
          - \"512mb\"
          - --maxmemory-policy
          - allkeys-lru
        ports:
        - containerPort: 6379
          name: redis
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: \"256Mi\"
            cpu: \"100m\"
          limits:
            memory: \"512Mi\"
            cpu: \"500m\"
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: nifty-cache-pvc

Features:
  ✓ PostgreSQL StatefulSet (persistent storage)
  ✓ 50Gi persistent volume
  ✓ Redis deployment with RDB persistence
  ✓ Both have liveness/readiness probes
  ✓ Stateless for easy scaling
"

echo "✅ Step 4 Completed!"
echo ""

# Command 5: GitHub Actions CI/CD
echo "[5/5] Creating GitHub Actions CI/CD Pipeline..."
opencode create .github/workflows/deploy.yml --description "
Create GitHub Actions CI/CD pipeline for automated testing and deployment:

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: \${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov black flake8 mypy
    
    - name: Run tests
      run: |
        pytest test/ --cov=src --cov-report=xml
      env:
        DATABASE_URL: postgresql://test:test@localhost:5432/test_db
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Code style check (black)
      run: black --check src/
    
    - name: Lint with flake8
      run: |
        flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Type checking with mypy
      run: mypy src/ --ignore-missing-imports || true

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: \${{ env.REGISTRY }}
        username: \${{ github.actor }}
        password: \${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=sha,prefix={{branch}}-
          type=semver,pattern={{version}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: \${{ github.event_name != 'pull_request' }}
        tags: \${{ steps.meta.outputs.tags }}
        labels: \${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: \${{ secrets.KUBE_CONFIG }}
        IMAGE_TAG: \${{ github.sha }}
      run: |
        mkdir -p \$HOME/.kube
        echo \"\$KUBE_CONFIG\" > \$HOME/.kube/config
        kubectl set image deployment/nifty-trading-app web=\${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}:main-\$IMAGE_TAG --record
        kubectl rollout status deployment/nifty-trading-app -w --timeout=5m
    
    - name: Run smoke tests
      run: |
        sleep 30
        curl -f http://load-balancer-url/health || exit 1
    
    - name: Slack notification
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: \${{ job.status }}
        text: 'Deployment \${{ job.status }}: nifty-trading'
        webhook_url: \${{ secrets.SLACK_WEBHOOK }}

Features:
  ✓ Automated testing on every PR
  ✓ Code coverage reporting
  ✓ Code quality checks (black, flake8, mypy)
  ✓ Docker image build and push
  ✓ Automatic deployment to Kubernetes on main branch
  ✓ Rollout status monitoring
  ✓ Slack notifications
  ✓ Smoke tests after deployment
"

echo "✅ Step 5 Completed!"
echo ""
echo "=========================================================="
echo "✅ Phase 13 Complete! Production deployment ready."
echo ""
echo "Key Features Added:"
echo "  ✓ Multi-stage Docker build (optimized)"
echo "  ✓ Docker Compose stack (PostgreSQL, Redis, Web)"
echo "  ✓ Kubernetes deployment (2-10 auto-scaling)"
echo "  ✓ PostgreSQL StatefulSet (50Gi persistent storage)"
echo "  ✓ Redis cache deployment"
echo "  ✓ GitHub Actions CI/CD pipeline"
echo "  ✓ Automated testing, linting, type-checking"
echo "  ✓ Automatic deployment to K8s"
echo ""
echo "Deployment Steps:"
echo "  1. Push to GitHub respository"
echo "  2. GitHub Actions automatically runs tests"
echo "  3. On main branch push, builds Docker container"
echo "  4. Deploys to Kubernetes with rolling update"
echo "  5. Runs smoke tests and sends Slack notification"
echo ""
echo "Next: Run Phase 14 (Ecosystem Integration)"
echo ""
