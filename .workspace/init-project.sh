#!/bin/bash
# Initialize a new project with pretext support
# Usage: ./init-project.sh <project-name>

if [ -z "$1" ]; then
    echo "Usage: ./init-project.sh <project-name>"
    exit 1
fi

PROJECT_NAME=$1
PROJECT_PATH="../$PROJECT_NAME"

echo "Creating new project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_PATH"

# Create package.json with pretext
cat > "$PROJECT_PATH/package.json" << 'EOF'
{
  "name": "${PROJECT_NAME}",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@chenglou/pretext": "latest"
  }
}
EOF

# Replace PROJECT_NAME in the file
sed -i "s/\${PROJECT_NAME}/$PROJECT_NAME/g" "$PROJECT_PATH/package.json"

echo "Project $PROJECT_NAME created with pretext support!"
echo "Run 'npm install' in the project directory to install dependencies."
