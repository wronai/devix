#!/bin/bash
# Docker commands for Devix containerization
# Supports building and running Devix in Docker containers

set -e

PACKAGE_NAME="devix"
ACTION="${1:-help}"

show_help() {
    echo "🐳 Devix Docker Management"
    echo ""
    echo "Usage: $0 [ACTION]"
    echo ""
    echo "Actions:"
    echo "  build    - Build Docker image"
    echo "  run      - Run Devix in Docker container" 
    echo "  shell    - Open interactive shell in container"
    echo "  clean    - Remove Docker images and containers"
    echo "  help     - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 run /workspace/myproject"
    echo "  $0 shell"
}

docker_build() {
    echo "🐳 Building Docker image for ${PACKAGE_NAME}..."
    
    if [ ! -f Dockerfile ]; then
        echo "❌ Dockerfile not found. Creating basic Dockerfile..."
        cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY . /app/

# Install Devix
RUN pip install -e .

# Set up entrypoint
ENTRYPOINT ["python", "-m", "devix"]
CMD ["analyze", "/workspace"]
EOF
        echo "✅ Basic Dockerfile created"
    fi
    
    docker build -t "${PACKAGE_NAME}:latest" .
    echo "✅ Docker image built successfully"
}

docker_run() {
    local workspace_path="${1:-$(pwd)/..}"
    echo "🐳 Running Devix in Docker..."
    echo "📁 Workspace: ${workspace_path}"
    
    docker run -it --rm \
        -v "${workspace_path}:/workspace" \
        "${PACKAGE_NAME}:latest" \
        analyze /workspace
}

docker_shell() {
    echo "🐳 Opening interactive shell in Docker container..."
    docker run -it --rm \
        -v "$(pwd)/..:/workspace" \
        "${PACKAGE_NAME}:latest" \
        /bin/bash
}

docker_clean() {
    echo "🐳 Cleaning Docker images and containers..."
    docker rmi "${PACKAGE_NAME}:latest" 2>/dev/null || echo "No image to remove"
    docker system prune -f
    echo "✅ Docker cleanup completed"
}

case "$ACTION" in
    "build")
        docker_build
        ;;
    "run")
        docker_run "$2"
        ;;
    "shell")
        docker_shell
        ;;
    "clean")
        docker_clean
        ;;
    "help"|*)
        show_help
        ;;
esac
