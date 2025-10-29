# GAON

## Automatic Environment Activation

To automatically activate the `gaon-venv` conda environment when you enter this project directory, you have several options:

### Option 1: Using the provided script
Run this command when you're in the project directory:
```bash
source activate_env.sh
```

### Option 2: Using the navigation function
1. Add the following function to your shell configuration file (`.zshrc` for zsh users or `.bashrc` for bash users):
```bash
# Function to navigate to the GAON project and activate the conda environment
cdgaon() {
    # Change to the GAON project directory
    cd /Users/hyunjunson/study/python/GAON
    
    # Check if conda is available
    if command -v conda &> /dev/null; then
        # Initialize conda if needed
        if [ -f "$(conda info --base)/etc/profile.d/conda.sh" ]; then
            source "$(conda info --base)/etc/profile.d/conda.sh"
        fi
        
        # Activate the gaon environment
        if conda env list | grep -q "^gaon-venv "; then
            conda activate gaon-venv
            echo "Activated conda environment: gaon-venv"
        else
            echo "Conda environment 'gaon-venv' not found. Please run setup.sh first."
        fi
    else
        echo "Conda not found. Please ensure conda is installed and in PATH."
    fi
}
```

2. After adding the function to your shell config, restart your terminal or run:
```bash
source ~/.zshrc  # or ~/.bashrc
```

3. Now you can simply run `cdgaon` to navigate to the project and activate the environment.

### Option 3: Using direnv (if installed)
If you have direnv installed, you can use the provided `.envrc` file by running:
```bash
direnv allow
```

Then the environment will be automatically activated when you enter the directory.

# this is test for changing my id
