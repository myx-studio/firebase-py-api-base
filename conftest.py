"""Root pytest configuration for the project."""
import sys
import os

# Add the functions directory to the system path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'functions')))