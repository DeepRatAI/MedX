#!/bin/bash
# =============================================================================
# MedeX - Docker Build and Deployment Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="medex"
VERSION="${MEDEX_VERSION:-1.0.0}"
REGISTRY="${DOCKER_REGISTRY:-}"

# Print functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    echo "MedeX Docker Build Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker images"
    echo "  push        Push images to registry"
    echo "  up          Start services"
    echo "  down        Stop services"
    echo "  logs        View logs"
    echo "  clean       Remove containers and images"
    echo "  test        Run tests in container"
    echo "  health      Check service health"
    echo ""
    echo "Options:"
    echo "  --target    Build target (production, development, ui, huggingface)"
    echo "  --tag       Image tag (default: latest)"
    echo "  --no-cache  Build without cache"
    echo ""
    echo "Examples:"
    echo "  $0 build --target production"
    echo "  $0 up"
    echo "  $0 logs api"
}

# Build function
build() {
    local TARGET="${1:-production}"
    local TAG="${2:-latest}"
    local NO_CACHE="${3:-}"
    
    print_header "Building MedeX Docker Image"
    echo "Target: $TARGET"
    echo "Tag: $TAG"
    
    local CACHE_FLAG=""
    if [ "$NO_CACHE" == "true" ]; then
        CACHE_FLAG="--no-cache"
    fi
    
    docker build \
        $CACHE_FLAG \
        --target "$TARGET" \
        --tag "${IMAGE_NAME}:${TAG}" \
        --tag "${IMAGE_NAME}:${TARGET}-${VERSION}" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VERSION="$VERSION" \
        .
    
    print_success "Image built: ${IMAGE_NAME}:${TAG}"
}

# Push function
push() {
    local TAG="${1:-latest}"
    
    if [ -z "$REGISTRY" ]; then
        print_error "DOCKER_REGISTRY not set"
        exit 1
    fi
    
    print_header "Pushing MedeX Docker Image"
    
    docker tag "${IMAGE_NAME}:${TAG}" "${REGISTRY}/${IMAGE_NAME}:${TAG}"
    docker push "${REGISTRY}/${IMAGE_NAME}:${TAG}"
    
    print_success "Image pushed: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
}

# Start services
up() {
    local PROFILE="${1:-}"
    
    print_header "Starting MedeX Services"
    
    if [ -n "$PROFILE" ]; then
        docker compose --profile "$PROFILE" up -d
    else
        docker compose up -d
    fi
    
    print_success "Services started"
    echo ""
    echo "API:    http://localhost:${MEDEX_API_PORT:-8000}"
    echo "UI:     http://localhost:${MEDEX_UI_PORT:-8501}"
    echo "Health: http://localhost:${MEDEX_API_PORT:-8000}/health"
}

# Stop services
down() {
    print_header "Stopping MedeX Services"
    docker compose down
    print_success "Services stopped"
}

# View logs
logs() {
    local SERVICE="${1:-}"
    
    if [ -n "$SERVICE" ]; then
        docker compose logs -f "$SERVICE"
    else
        docker compose logs -f
    fi
}

# Clean up
clean() {
    print_header "Cleaning MedeX Docker Resources"
    
    print_warning "Stopping containers..."
    docker compose down -v --remove-orphans 2>/dev/null || true
    
    print_warning "Removing images..."
    docker rmi $(docker images "${IMAGE_NAME}" -q) 2>/dev/null || true
    
    print_warning "Pruning unused resources..."
    docker system prune -f
    
    print_success "Cleanup complete"
}

# Run tests in container
test() {
    print_header "Running Tests in Container"
    
    docker compose run --rm api python -m pytest tests/ -v --tb=short
    
    print_success "Tests complete"
}

# Health check
health() {
    print_header "Checking Service Health"
    
    echo -n "API: "
    if curl -sf http://localhost:${MEDEX_API_PORT:-8000}/health > /dev/null; then
        print_success "Healthy"
    else
        print_error "Unhealthy"
    fi
    
    echo -n "UI:  "
    if curl -sf http://localhost:${MEDEX_UI_PORT:-8501}/healthz > /dev/null; then
        print_success "Healthy"
    else
        print_error "Unhealthy"
    fi
}

# Parse arguments
COMMAND="${1:-help}"
shift || true

TARGET="production"
TAG="latest"
NO_CACHE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="true"
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Execute command
case $COMMAND in
    build)
        build "$TARGET" "$TAG" "$NO_CACHE"
        ;;
    push)
        push "$TAG"
        ;;
    up)
        up "$1"
        ;;
    down)
        down
        ;;
    logs)
        logs "$1"
        ;;
    clean)
        clean
        ;;
    test)
        test
        ;;
    health)
        health
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
