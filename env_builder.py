#!/usr/bin/env python3
"""
Virtual Environment Builder for Linux Hardware Diagnostic.
Creates and configures the Python virtual environment automatically.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


class Colors:
    """ANSI colors for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class EnvBuilder:
    """Virtual environment builder."""
    
    def __init__(self, venv_name: str = "venv"):
        self.project_root = Path(__file__).parent.absolute()
        self.venv_path = self.project_root / venv_name
        self.requirements_file = self.project_root / "requirements.txt"
        self.python_executable = sys.executable
    
    def print_step(self, message: str):
        """Print a step message."""
        print(f"{Colors.BLUE}==>{Colors.RESET} {Colors.BOLD}{message}{Colors.RESET}")
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"{Colors.RED}✗{Colors.RESET} {message}")
    
    def check_python_version(self) -> bool:
        """Check that Python is >= 3.8."""
        if sys.version_info < (3, 8):
            self.print_error(f"Python 3.8+ is required. Current version: {sys.version}")
            return False
        self.print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True
    
    def create_venv(self) -> bool:
        """Create the virtual environment."""
        try:
            self.print_step(f"Creating virtual environment in {self.venv_path}")
            
            if self.venv_path.exists():
                self.print_warning(f"Virtual environment already exists: {self.venv_path}")
                response = input("Do you want to recreate it? [y/N]: ").strip().lower()
                if response == 'y':
                    import shutil
                    shutil.rmtree(self.venv_path)
                    self.print_success("Existing venv removed")
                else:
                    self.print_warning("Keeping existing venv")
                    return True
            
            # On WSL paths mounted from Windows (e.g. /mnt/c), creating symlinks
            # can fail with EPERM. Force copies for broader compatibility.
            venv.create(self.venv_path, with_pip=True, clear=True, symlinks=False)
            self.print_success(f"Virtual environment created: {self.venv_path}")
            return True
            
        except Exception as e:
            self.print_error(f"Error while creating venv: {e}")
            return False
    
    def get_venv_python(self) -> Path:
        """Get the Python executable path inside the venv."""
        if os.name == 'nt':  # Windows
            return self.venv_path / "Scripts" / "python.exe"
        else:  # Linux/Mac
            return self.venv_path / "bin" / "python"
    
    def get_venv_pip(self) -> Path:
        """Get the pip executable path inside the venv."""
        if os.name == 'nt':  # Windows
            return self.venv_path / "Scripts" / "pip.exe"
        else:  # Linux/Mac
            return self.venv_path / "bin" / "pip"
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip to the latest version."""
        try:
            self.print_step("Upgrading pip...")
            
            python_path = self.get_venv_python()
            
            # Use `python -m pip` instead of calling pip directly for reliability.
            result = subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.print_success("pip upgraded")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Error while upgrading pip: {e.stderr}")
            return False
        except FileNotFoundError as e:
            self.print_error(f"Python executable not found in venv: {e}")
            return False
    
    def install_requirements(self) -> bool:
        """Install dependencies from requirements.txt."""
        try:
            if not self.requirements_file.exists():
                self.print_warning(f"File not found: {self.requirements_file}")
                return False
            
            self.print_step(f"Installing dependencies from {self.requirements_file.name}")
            
            python_path = self.get_venv_python()
            
            # Use `python -m pip` instead of calling pip directly for reliability.
            result = subprocess.run(
                [str(python_path), "-m", "pip", "install", "-r", str(self.requirements_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.print_success("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Error while installing dependencies:\n{e.stderr}")
            return False
        except FileNotFoundError as e:
            self.print_error(f"Python executable not found in venv: {e}")
            return False
    
    def show_activation_instructions(self):
        """Show instructions to activate the venv."""
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Setup completed!{Colors.RESET}\n")
        print("To activate the virtual environment:")
        
        if os.name == 'nt':  # Windows
            print(f"  {Colors.YELLOW}{self.venv_path}\\Scripts\\activate{Colors.RESET}")
        else:  # Linux/Mac
            print(f"  {Colors.YELLOW}source {self.venv_path}/bin/activate{Colors.RESET}")
        
        print("\nTo run the program:")
        print(f"  {Colors.YELLOW}python cli.py --help{Colors.RESET}")
        print(f"\nTo deactivate:")
        print(f"  {Colors.YELLOW}deactivate{Colors.RESET}\n")
    
    def build(self) -> bool:
        """Run the full setup process."""
        print(f"\n{Colors.BOLD}=== Linux Hardware Diagnostic - Environment Builder ==={Colors.RESET}\n")
        
        # Step 1: Check Python version.
        if not self.check_python_version():
            return False
        
        # Step 2: Create venv.
        if not self.create_venv():
            return False
        
        # Step 3: Upgrade pip.
        if not self.upgrade_pip():
            self.print_warning("Continuing with current pip version")
        
        # Step 4: Install requirements.
        if not self.install_requirements():
            return False
        
        # Step 5: Show activation instructions.
        self.show_activation_instructions()
        
        return True


def main():
    """Script entry point."""
    builder = EnvBuilder(venv_name="venv")
    
    try:
        success = builder.build()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
