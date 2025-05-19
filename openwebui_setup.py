import os
import sys
import shutil
import subprocess
from pathlib import Path

def setup_openwebui():
   """Download and set up OpenWebUI for the MCP demo."""
   webui_dir = Path("./webui")
   
   # Check if webui directory already exists
   if webui_dir.exists():
       print("OpenWebUI directory already exists. Would you like to reinstall? (y/n)")
       choice = input().strip().lower()
       if choice == 'y':
           shutil.rmtree(webui_dir)
       else:
           print("Skipping OpenWebUI setup")
           return
   
   print("Setting up OpenWebUI...")
   
   # Clone the OpenWebUI repository
   subprocess.run(["git", "clone", "https://github.com/open-webui/open-webui.git", "temp_webui"], check=True)
   
   # Create webui directory
   webui_dir.mkdir(exist_ok=True)
   
   # Copy frontend build files
   frontend_dir = Path("temp_webui/frontend/dist")
   if not frontend_dir.exists():
       print("Building OpenWebUI frontend...")
       os.chdir("temp_webui/frontend")
       subprocess.run(["npm", "install"], check=True)
       subprocess.run(["npm", "run", "build"], check=True)
       os.chdir("../..")
   
   # Copy the built frontend to webui directory
   print("Copying OpenWebUI frontend files...")
   shutil.copytree("temp_webui/frontend/dist", "webui", dirs_exist_ok=True)
   
   # Clean up temporary directory
   shutil.rmtree("temp_webui")
   
   # Create config file for OpenWebUI
   config_file = webui_dir / "openwebui-config.js"
   with open(config_file, "w") as f:
       f.write("""
// OpenWebUI configuration for MCP integration
window.OPENWEBUI_CONFIG = {
   // API endpoint for the MCP agent
   agentApiEndpoint: '/api/agent',
   
   // Default model configuration
   defaultModel: 'mcp-agent',
   
   // Available models
   models: [
       {
           id: 'mcp-agent',
           name: 'MCP Agent (GPT-4o-mini)',
           description: 'Agent with Brave Search and Google Maps capabilities',
           contextLength: 16000,
           interfaces: ['chat'],
       }
   ],
   
   // Custom UI theme
   theme: {
       name: 'MCP Demo',
       primaryColor: '#3b82f6',
       backgroundColor: '#0f172a',
   },
   
   // Enable debug mode for development
   debug: true
};
""")
   
   print("OpenWebUI setup complete!")

if __name__ == "__main__":
   setup_openwebui()