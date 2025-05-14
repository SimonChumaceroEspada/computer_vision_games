#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Computer Vision Games Menu System

This script provides a user-friendly menu interface for selecting and launching
different computer vision game controllers in the project. It includes options
to test the camera, adjust settings, and launch each available game.

Requirements:
- Python 3.10
- OpenCV
- PyAutoGUI
- Tkinter
"""

import os
import sys
import cv2
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, font
import importlib.util
import threading

# Import camera detection utility
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from camera_detector import list_available_cameras, test_camera_view

class ComputerVisionGamesMenu:
    """Main menu interface for the Computer Vision Games project"""
    
    def __init__(self, root):
        """Initialize the menu system"""
        self.root = root
        self.root.title("Computer Vision Games")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.configure(bg="#2c3e50")
        
        # Set application icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
            
        # Store available cameras
        self.cameras = []
        self.selected_camera = tk.IntVar(value=0)
        
        # Create header
        self.create_header()
        
        # Create main content
        self.create_main_content()
        
        # Create footer
        self.create_footer()
        
        # Load available cameras
        self.load_cameras()
        
    def create_header(self):
        """Create the header with title and instructions"""
        header_frame = tk.Frame(self.root, bg="#34495e", padx=20, pady=15)
        header_frame.pack(fill=tk.X)
        
        # Title
        title_font = font.Font(family="Segoe UI", size=24, weight="bold")
        title = tk.Label(header_frame, text="Computer Vision Games", 
                        font=title_font, bg="#34495e", fg="white")
        title.pack()
        
        # Subtitle
        subtitle_font = font.Font(family="Segoe UI", size=12)
        subtitle = tk.Label(header_frame, 
                           text="Control your favorite games using computer vision", 
                           font=subtitle_font, bg="#34495e", fg="#bdc3c7")
        subtitle.pack(pady=5)
    
    def create_main_content(self):
        """Create the main content area with camera settings and game options"""
        content_frame = tk.Frame(self.root, bg="#2c3e50", padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel for camera settings
        left_panel = tk.LabelFrame(content_frame, text="Camera Settings", 
                                 bg="#2c3e50", fg="white", padx=15, pady=15)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Camera selection
        camera_label = tk.Label(left_panel, text="Select Camera:", 
                              bg="#2c3e50", fg="white")
        camera_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.camera_listbox = tk.Listbox(left_panel, height=5)
        self.camera_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # Refresh cameras button
        refresh_btn = ttk.Button(left_panel, text="Refresh Cameras", 
                                command=self.load_cameras)
        refresh_btn.pack(fill=tk.X, pady=5)
        
        # Test camera button
        test_btn = ttk.Button(left_panel, text="Test Selected Camera", 
                             command=self.test_selected_camera)
        test_btn.pack(fill=tk.X, pady=5)
        
        # Right panel for games
        right_panel = tk.LabelFrame(content_frame, text="Available Games", 
                                  bg="#2c3e50", fg="white", padx=15, pady=15)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Game buttons with descriptive text
        self.create_game_button(right_panel, 
                              "Arcade 1942", 
                              "Control the classic shoot-em-up game with hand gestures",
                              self.launch_arcade_1942)
        
        self.create_game_button(right_panel, 
                              "Geometry Dash", 
                              "Play the rhythm-based platformer with hand gestures",
                              self.launch_geometry_dash)
        
        self.create_game_button(right_panel, 
                              "Subway Surfers", 
                              "Control the endless runner using full-body pose detection",
                              self.launch_subway_surfers)
    
    def create_footer(self):
        """Create the footer with credits and exit button"""
        footer_frame = tk.Frame(self.root, bg="#34495e", padx=20, pady=15)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Credits label
        credits = tk.Label(footer_frame, 
                          text="Computer Vision Games - May 2025", 
                          bg="#34495e", fg="#bdc3c7")
        credits.pack(side=tk.LEFT)
        
        # Exit button
        exit_btn = ttk.Button(footer_frame, text="Exit", command=self.root.destroy)
        exit_btn.pack(side=tk.RIGHT)
    
    def create_game_button(self, parent, title, description, command):
        """Create a styled button for a game with description"""
        game_frame = tk.Frame(parent, bg="#2c3e50", pady=5)
        game_frame.pack(fill=tk.X, pady=5)
        
        # Game title
        title_font = font.Font(family="Segoe UI", size=12, weight="bold")
        title_label = tk.Label(game_frame, text=title, 
                             font=title_font, bg="#2c3e50", fg="white", 
                             anchor=tk.W)
        title_label.pack(fill=tk.X)
        
        # Game description
        desc_label = tk.Label(game_frame, text=description, 
                            bg="#2c3e50", fg="#bdc3c7", 
                            wraplength=300, justify=tk.LEFT)
        desc_label.pack(fill=tk.X, pady=(0, 5))
        
        # Launch button
        launch_btn = ttk.Button(game_frame, text=f"Launch {title}", 
                               command=command)
        launch_btn.pack(fill=tk.X)
    
    def load_cameras(self):
        """Load all available cameras and update the UI"""
        self.camera_listbox.delete(0, tk.END)
        
        # Get available cameras
        self.cameras = list_available_cameras()
        
        if not self.cameras:
            self.camera_listbox.insert(tk.END, "No cameras detected")
        else:
            for idx, cam_id in enumerate(self.cameras):
                self.camera_listbox.insert(tk.END, f"Camera {cam_id}")
            
            # Select the first camera by default
            self.camera_listbox.selection_set(0)
    
    def get_selected_camera_id(self):
        """Get the ID of the currently selected camera"""
        selection = self.camera_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a camera")
            return None
        
        index = selection[0]
        if index >= len(self.cameras):
            messagebox.showerror("Error", "Invalid camera selection")
            return None
        
        return self.cameras[index]
    
    def test_selected_camera(self):
        """Test the currently selected camera"""
        camera_id = self.get_selected_camera_id()
        if camera_id is not None:
            # Run the camera test in a separate thread to avoid freezing the UI
            threading.Thread(target=test_camera_view, args=(camera_id,), daemon=True).start()
    
    def launch_game(self, script_name, message):
        """Launch a game script with the selected camera"""
        camera_id = self.get_selected_camera_id()
        if camera_id is not None:
            try:
                # Check if the script exists
                script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
                if not os.path.exists(script_path):
                    messagebox.showerror("Error", f"Game script not found: {script_name}")
                    return
                
                # Launch the game in a separate process
                messagebox.showinfo("Launching Game", message)
                
                # Handle different parameter structures for different games
                command = [sys.executable, script_path]
                
                # Special handling for arcade_1942_mouse_controller.py which requires different parameter format
                if "arcade_1942_mouse_controller.py" in script_name:
                    command.extend(["--play", f"--camera={str(camera_id)}"])
                # Special handling for subway_surfers_pose_detection.py which doesn't accept camera parameter
                elif "subway_surfers_pose_detection.py" in script_name:
                    command.extend(["--play"])
                # Default handling for other games (geometry dash, etc.)
                else:
                    command.extend(["--play", "--camera", str(camera_id)])
                
                # Run the game script with the appropriate parameters
                subprocess.Popen(command)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch game: {str(e)}")
    
    def launch_arcade_1942(self):
        """Launch the Arcade 1942 game controller"""
        self.launch_game(
            "arcade_1942_mouse_controller.py", 
            "Launching Arcade 1942 controller. Use hand gestures to control the game!"
        )
    
    def launch_geometry_dash(self):
        """Launch the Geometry Dash game controller"""
        self.launch_game(
            "geometry_dash_hand_controller.py", 
            "Launching Geometry Dash controller. Use hand gestures to jump and navigate!"
        )
    
    def launch_subway_surfers(self):
        """Launch the Subway Surfers game controller"""
        self.launch_game(
            "subway_surfers_pose_detection.py", 
            "Launching Subway Surfers controller. Use body poses to control the game!"
        )

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = ComputerVisionGamesMenu(root)
    root.mainloop()

if __name__ == "__main__":
    main()