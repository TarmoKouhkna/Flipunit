#!/bin/bash

# Comprehensive Deployment Script for FlipUnit.eu
# Run this script on your VPS server at /opt/flipunit
# Usage: ./deploy.sh [--skip-build] [--skip-migrations]

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/flipunit"
BRANCH="main"
SKIP_BUILD=false
SKIP_MIGRATIONS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   FlipUnit.eu Deployment Script        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
    echo "Please run this script from /opt/flipunit"
    exit 1
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}✓ Working directory: $(pwd)${NC}"
echo ""

# Step 1: Check Git status
echo -e "${BLUE}Step 1: Checking Git status...${NC}"
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not a git repository!${NC}"
    exit 1
fi

CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}✓ Current branch: $CURRENT_BRANCH${NC}"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    echo "   Files with changes:"
    git status --short | head -5
    echo ""
    echo "   Continue anyway? (y/n)"
    read -r CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi
echo ""

# Step 2: Pull latest code
echo -e "${BLUE}Step 2: Pulling latest code from $BRANCH...${NC}"
git fetch origin
git pull origin "$BRANCH"
LATEST_COMMIT=$(git rev-parse --short HEAD)
echo -e "${GREEN}✓ Latest commit: $LATEST_COMMIT${NC}"
echo ""

# Step 3: Check environment variables
echo -e "${BLUE}Step 3: Checking environment variables...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo "   Creating .env from .env.example if it exists..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}   ⚠️  Please edit .env file with your actual values!${NC}"
    else
        echo -e "${RED}   ❌ .env.example not found either!${NC}"
        echo "   Required environment variables:"
        echo "   - SECRET_KEY (generate new one for production!)"
        echo "   - DEBUG=False"
        echo "   - ALLOWED_HOSTS=flipunit.eu,www.flipunit.eu,217.146.78.140"
        echo "   - DB_NAME, DB_USER, DB_PASSWORD"
        echo "   - SITE_URL=https://flipunit.eu"
    fi
else
    # Check critical variables
    source .env 2>/dev/null || true
    if [ -z "$SECRET_KEY" ]; then
        echo -e "${RED}   ❌ SECRET_KEY not set in .env!${NC}"
        echo "   Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
        exit 1
    fi
    if [ "$DEBUG" != "False" ] && [ "$DEBUG" != "false" ]; then
        echo -e "${YELLOW}   ⚠️  DEBUG is not set to False in .env${NC}"
    fi
    echo -e "${GREEN}   ✓ Environment variables check passed${NC}"
fi
echo ""

# Step 4: Check Docker
echo -e "${BLUE}Step 4: Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker: $(docker --version)${NC}"
echo -e "${GREEN}✓ Docker Compose: $(docker-compose --version)${NC}"
echo ""

# Step 5: Build Docker images (if needed)
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${BLUE}Step 5: Building Docker images...${NC}"
    echo "   This may take a few minutes..."
    docker-compose build --no-cache
    echo -e "${GREEN}✓ Docker images built successfully${NC}"
    echo ""
else
    echo -e "${YELLOW}Step 5: Skipping Docker build (--skip-build)${NC}"
    echo ""
fi

# Step 6: Stop containers
echo -e "${BLUE}Step 6: Stopping containers...${NC}"
docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 7: Start containers
echo -e "${BLUE}Step 7: Starting containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for containers to be ready
echo "   Waiting for containers to be ready..."
sleep 5

# Step 8: Run migrations
if [ "$SKIP_MIGRATIONS" = false ]; then
    echo -e "${BLUE}Step 8: Running database migrations...${NC}"
    docker-compose exec -T web python manage.py migrate --noinput
    echo -e "${GREEN}✓ Migrations completed${NC}"
    echo ""
else
    echo -e "${YELLOW}Step 8: Skipping migrations (--skip-migrations)${NC}"
    echo ""
fi

# Step 9: Collect static files
echo -e "${BLUE}Step 9: Collecting static files...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

# Step 10: Verify deployment
echo -e "${BLUE}Step 10: Verifying deployment...${NC}"

# Check container status
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Containers are running${NC}"
else
    echo -e "${RED}❌ Some containers are not running!${NC}"
    docker-compose ps
    exit 1
fi

# Check web container health
if docker-compose exec -T web python manage.py check --deploy 2>/dev/null; then
    echo -e "${GREEN}✓ Django system check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Django system check had warnings (this may be normal)${NC}"
fi

# Test if web server responds
echo "   Testing web server..."
sleep 2
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ Web server is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Web server may not be responding yet (check logs)${NC}"
fi
echo ""

# Step 11: Show container logs (last 10 lines)
echo -e "${BLUE}Step 11: Recent container logs...${NC}"
docker-compose logs --tail=10 web
echo ""

# Final summary
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Deployment Complete!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "   • Branch: $BRANCH"
echo "   • Commit: $LATEST_COMMIT"
echo "   • Containers: $(docker-compose ps -q | wc -l) running"
echo ""
echo -e "${BLUE}🔍 Next Steps:${NC}"
echo "   1. Check logs: docker-compose logs -f web"
echo "   2. Test website: https://flipunit.eu"
echo "   3. Verify new features:"
echo "      - Gold price converter"
echo "      - Updated branding (flipunit logo)"
echo "      - HTML to PDF (with WeasyPrint)"
echo ""
echo -e "${BLUE}🛠️  Useful Commands:${NC}"
echo "   • View logs: docker-compose logs -f web"
echo "   • Restart: docker-compose restart web"
echo "   • Stop: docker-compose down"
echo "   • Shell access: docker-compose exec web bash"
echo ""
echo -e "${GREEN}✨ All done! Your changes are now live.${NC}"















