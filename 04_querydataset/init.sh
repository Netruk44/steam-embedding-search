
#!/bin/bash

venv_dir=".venv_04"

# Check if .venv directory exists
if [ -d "$venv_dir" ]; then
  echo "The .venv directory already exists."
  exit 1
fi

# Create .venv directory
echo "Creating .venv directory..."
python3 -m venv "$venv_dir"

# Activate .venv
echo "Activating .venv..."
source "$venv_dir/bin/activate"

# Install packages from requirements.txt
echo "Installing packages from requirements.txt..."
pip install -r requirements.txt

# Deactivate .venv
deactivate

echo ""
echo "Environment created, activate with:"
echo "source \"$venv_dir/bin/activate\""