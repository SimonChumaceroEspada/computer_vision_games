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
- Pillow (PIL)
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
from PIL import Image, ImageTk

# Import camera detection utility
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from camera_detector import list_available_cameras, test_camera_view

class ComputerVisionGamesMenu:
    """Main menu interface for the Computer Vision Games project"""        
    def __init__(self, root):
        """Initialize the menu system"""
        self.root = root
        self.root.title("Juegos de Visión por Computadora")
          # Optimal resolution for maximum compatibility
        optimal_width = 1024
        optimal_height = 768
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - optimal_width) // 2
        y = (screen_height - optimal_height) // 2
        
        self.root.geometry(f"{optimal_width}x{optimal_height}+{x}+{y}")
        self.root.minsize(800, 600)  # Minimum size for usability
        self.root.maxsize(1400, 1000)  # Maximum size to prevent over-stretching
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.colors = {
            'primary': '#1a1a2e',      # Deep navy blue
            'secondary': '#16213e',     # Darker blue
            'accent': '#0f3460',        # Blue accent
            'highlight': '#533483',     # Purple highlight
            'text_primary': '#ffffff',  # White text
            'text_secondary': '#b0b3c1', # Light gray
            'success': '#4ade80',       # Green
            'warning': '#fbbf24',       # Yellow
            'error': '#f87171'          # Red
        }
        
        self.root.configure(bg=self.colors['primary'])
        
        # Configure ttk styles
        self.setup_styles()
        
        # Set application icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
            
        # Store available cameras
        self.cameras = []
        self.selected_camera = tk.IntVar(value=0)
        
        # Load and store images
        self.load_images()
        
        # Create main canvas with scrolling capability
        self.create_scrollable_canvas()
        
        # Create header
        self.create_header()
        
        # Create main content
        self.create_main_content()
        
        # Create footer
        self.create_footer()
          # Load available cameras
        self.load_cameras()
        
        # Initial responsive layout setup
        self.root.after(100, self.create_responsive_layout)
        
    def setup_styles(self):
        """Configure custom ttk styles for a modern look"""
        style = ttk.Style()        # Configure button style with black text for better visibility
        style.configure('Game.TButton',
                       background=self.colors['accent'],
                       foreground='#000000',  # Black text for better visibility
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 10))
        
        style.map('Game.TButton',
                 background=[('active', self.colors['highlight']),
                            ('pressed', self.colors['secondary'])],
                 foreground=[('active', '#000000'),  # Keep black when active
                            ('pressed', '#000000')])  # Keep black when pressed
          # Configure smaller button style with black text for better visibility
        style.configure('Small.TButton',
                       background=self.colors['secondary'],
                       foreground='#000000',  # Black text for better visibility
                       font=('Segoe UI', 9),
                       padding=(10, 8))
        
        style.map('Small.TButton',
                 background=[('active', self.colors['accent']),
                            ('pressed', self.colors['highlight'])],
                 foreground=[('active', '#000000'),  # Keep black when active
                            ('pressed', '#000000')])  # Keep black when pressed
    
    def load_images(self):
        """Load and resize images for the interface"""
        self.images = {}
        img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imgs")
        
        # Game images mapping
        image_files = {
            'arcade_1942': ('1942_icon.png', '1942_wallpaper.jpg'),
            'geometry_dash': ('Logo_of_Geometry_Dash.svg.png', 'geometry_dash_wallpaper.jpg'),
            'subway_surfers': ('subway_surfers_icon.png', 'subway_surfers_wallpaper.jpg')
        }
        
        for game, (icon_file, wallpaper_file) in image_files.items():
            try:
                # Load icon (square format)
                icon_path = os.path.join(img_dir, icon_file)
                if os.path.exists(icon_path):
                    icon_img = Image.open(icon_path)
                    icon_img = icon_img.resize((64, 64), Image.Resampling.LANCZOS)
                    self.images[f'{game}_icon'] = ImageTk.PhotoImage(icon_img)
                
                # Load wallpaper (for background or card backgrounds)
                wallpaper_path = os.path.join(img_dir, wallpaper_file)
                if os.path.exists(wallpaper_path):
                    wallpaper_img = Image.open(wallpaper_path)
                    wallpaper_img = wallpaper_img.resize((300, 150), Image.Resampling.LANCZOS)
                    self.images[f'{game}_wallpaper'] = ImageTk.PhotoImage(wallpaper_img)
                    
                    # Create a smaller version for cards
                    card_img = Image.open(wallpaper_path)
                    card_img = card_img.resize((200, 120), Image.Resampling.LANCZOS)
                    self.images[f'{game}_card'] = ImageTk.PhotoImage(card_img)
                    
            except Exception as e:
                print(f"Could not load image for {game}: {e}")
    
    def create_scrollable_canvas(self):
        """Create a scrollable canvas for responsive design"""
        # Create main frame that will contain everything
        self.main_frame = tk.Frame(self.root, bg=self.colors['primary'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame, bg=self.colors['primary'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['primary'])
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_header(self):
        """Create the header with title and instructions"""
        header_frame = tk.Frame(self.scrollable_frame, bg=self.colors['secondary'], padx=30, pady=25)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 0))
        
        # Create gradient effect with multiple frames
        gradient_frame = tk.Frame(header_frame, bg=self.colors['secondary'])
        gradient_frame.pack(fill=tk.X)
        
        # Title with shadow effect
        title_font = font.Font(family="Segoe UI", size=28, weight="bold")
          # Shadow text
        shadow_title = tk.Label(gradient_frame, text="Juegos de Visión por Computadora", 
                              font=title_font, bg=self.colors['secondary'], 
                              fg=self.colors['primary'])
        shadow_title.pack(pady=(2, 0))
        
        # Main title
        title = tk.Label(gradient_frame, text="Juegos de Visión por Computadora", 
                        font=title_font, bg=self.colors['secondary'], 
                        fg=self.colors['text_primary'])
        title.place(in_=shadow_title, x=-2, y=-2)
        
        # Subtitle with icon-like decoration
        subtitle_frame = tk.Frame(gradient_frame, bg=self.colors['secondary'])
        subtitle_frame.pack(pady=(10, 0))
        
        # Decorative elements
        left_line = tk.Frame(subtitle_frame, bg=self.colors['highlight'], height=2, width=50)
        left_line.pack(side=tk.LEFT, pady=8)        
        subtitle_font = font.Font(family="Segoe UI", size=14, weight="normal")
        subtitle = tk.Label(subtitle_frame, 
                           text="  🎮 Controla tus juegos favoritos usando visión por computadora  🎮", 
                           font=subtitle_font, bg=self.colors['secondary'], 
                           fg=self.colors['text_secondary'])
        subtitle.pack(side=tk.LEFT, padx=10)
        
        right_line = tk.Frame(subtitle_frame, bg=self.colors['highlight'], height=2, width=50)
        right_line.pack(side=tk.RIGHT, pady=8)
        
    def create_main_content(self):
        """Create the main content area with camera settings and game options"""
        # Main container with responsive design
        main_container = tk.Frame(self.scrollable_frame, bg=self.colors['primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Camera settings panel - full width
        self.create_camera_panel(main_container)
        
        # Games grid - responsive
        self.create_games_grid(main_container)
    def create_camera_panel(self, parent):
        """Create the camera settings panel"""
        camera_frame = tk.LabelFrame(parent, text="🎥 Configuración de Cámara", 
                                   bg=self.colors['secondary'], fg=self.colors['text_primary'],
                                   font=('Segoe UI', 12, 'bold'), padx=20, pady=15,
                                   relief='flat', bd=2)
        camera_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Camera selection with modern styling
        selection_frame = tk.Frame(camera_frame, bg=self.colors['secondary'])
        selection_frame.pack(fill=tk.X, pady=(0, 15))        
        camera_label = tk.Label(selection_frame, text="Seleccionar Cámara:", 
                              bg=self.colors['secondary'], fg=self.colors['text_primary'],
                              font=('Segoe UI', 10, 'bold'))
        camera_label.pack(anchor=tk.W, pady=(0, 8))
        
        # Custom listbox with better styling
        listbox_frame = tk.Frame(selection_frame, bg=self.colors['accent'], relief='flat', bd=1)
        listbox_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.camera_listbox = tk.Listbox(listbox_frame, height=4, 
                                       bg=self.colors['primary'], 
                                       fg=self.colors['text_primary'],
                                       selectbackground=self.colors['highlight'],
                                       font=('Segoe UI', 9),
                                       relief='flat', bd=0)
        self.camera_listbox.pack(fill=tk.X, padx=2, pady=2)
        
        # Button container
        button_frame = tk.Frame(camera_frame, bg=self.colors['secondary'])
        button_frame.pack(fill=tk.X)
          # Refresh cameras button
        refresh_btn = ttk.Button(button_frame, text="🔄 Actualizar Cámaras", 
                                command=self.load_cameras, style='Small.TButton')
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        # Test camera button
        test_btn = ttk.Button(button_frame, text="🔍 Probar Cámara", 
                             command=self.test_selected_camera, style='Small.TButton')
        test_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)        
    def create_games_grid(self, parent):
        """Create a modern grid layout for games"""
        games_frame = tk.LabelFrame(parent, text="🎮 Juegos Disponibles", 
                                  bg=self.colors['secondary'], fg=self.colors['text_primary'],
                                  font=('Segoe UI', 12, 'bold'), padx=20, pady=15,
                                  relief='flat', bd=2)
        games_frame.pack(fill=tk.BOTH, expand=True)
          # Create a responsive container that adapts to window size
        self.games_container = tk.Frame(games_frame, bg=self.colors['secondary'])
        self.games_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Store game data
        self.games_data = [
            {
                'name': 'Arcade 1942',
                'description': 'Controla el clásico juego de disparos con gestos intuitivos de las manos',
                'image_key': 'arcade_1942',
                'command': self.launch_arcade_1942,
                'color': '#ff6b6b'
            },
            {
                'name': 'Geometry Dash',
                'description': 'Navega por el juego de plataformas rítmico usando movimientos precisos de las manos',
                'image_key': 'geometry_dash',
                'command': self.launch_geometry_dash,
                'color': '#4ecdc4'
            },
            {
                'name': 'Subway Surfers',
                'description': 'Controla el juego de correr infinito con detección de poses de todo el cuerpo',
                'image_key': 'subway_surfers',
                'command': self.launch_subway_surfers,
                'color': '#45b7d1'
            }
        ]
        
        # Create responsive layout
        self.create_responsive_layout()
        
        # Bind window resize event for responsive behavior        self.root.bind('<Configure>', self.on_responsive_resize)        
    def create_responsive_layout(self):
        """Create compact layout with 3 games in a row for 1024x768"""
        # Clear any existing game cards
        for widget in self.games_container.winfo_children():
            widget.destroy()
        
        # 3 columns layout - one game per column for compact design
        cols = 3
        
        # Create game cards in 3-column grid (all in one row)
        for i, game in enumerate(self.games_data):
            row = 0  # All games in first row
            col = i  # Each game gets its own column
            self.create_game_card(self.games_container, game, row, col)
        
        # Configure grid weights for optimal spacing
        for i in range(cols):
            self.games_container.columnconfigure(i, weight=1)
            
        # Configure row weight
        self.games_container.rowconfigure(0, weight=1)        
    def on_responsive_resize(self, event):
        """Handle window resize - maintain optimal layout"""
        # Only respond to root window resize events
        if event.widget == self.root:
            # Maintain the 3-column layout for consistency
            self.root.after(100, self.create_responsive_layout)
    
    def create_game_card(self, parent, game_data, row, col):
        """Create a compact game card optimized for 3-column layout"""
        # Card frame with responsive behavior - more compact padding
        card_frame = tk.Frame(parent, bg=self.colors['accent'], relief='flat', bd=1)
        card_frame.grid(row=row, column=col, padx=5, pady=8, sticky="nsew")
        
        # Make card expand to fill available space
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(0, weight=1)
          # Inner content frame - more compact padding for 3-column layout
        content_frame = tk.Frame(card_frame, bg=self.colors['accent'], padx=8, pady=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with icon and title
        header_frame = tk.Frame(content_frame, bg=self.colors['accent'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Game icon
        icon_key = f"{game_data['image_key']}_icon"
        if icon_key in self.images:
            icon_label = tk.Label(header_frame, image=self.images[icon_key], 
                                bg=self.colors['accent'])
            icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Title and description container
        text_frame = tk.Frame(header_frame, bg=self.colors['accent'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Game title
        title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        title_label = tk.Label(text_frame, text=game_data['name'], 
                             font=title_font, bg=self.colors['accent'], 
                             fg=self.colors['text_primary'], anchor=tk.W)
        title_label.pack(fill=tk.X)
          # Game description - more compact for 3-column layout
        desc_font = font.Font(family="Segoe UI", size=8)
        desc_label = tk.Label(text_frame, text=game_data['description'], 
                            font=desc_font, bg=self.colors['accent'], 
                            fg=self.colors['text_secondary'], 
                            wraplength=180, justify=tk.LEFT, anchor=tk.W)
        desc_label.pack(fill=tk.X, pady=(3, 0))
        
        # Background image (if available)
        card_key = f"{game_data['image_key']}_card"
        if card_key in self.images:
            # Create image frame
            img_frame = tk.Frame(content_frame, bg=self.colors['accent'], height=100)
            img_frame.pack(fill=tk.X, pady=(0, 15))
            img_frame.pack_propagate(False)
            
            img_label = tk.Label(img_frame, image=self.images[card_key], 
                               bg=self.colors['accent'])
            img_label.pack(expand=True)        # Launch button with custom styling - more compact
        launch_btn = ttk.Button(content_frame, text=f"🚀 Lanzar {game_data['name']}", 
                               command=game_data['command'], style='Game.TButton')
        launch_btn.pack(fill=tk.X, pady=(8, 0))
    def create_footer(self):
        """Create the footer with credits and exit button"""
        footer_frame = tk.Frame(self.scrollable_frame, bg=self.colors['secondary'], padx=30, pady=20)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(20, 20))
        
        # Credits section with modern styling
        credits_frame = tk.Frame(footer_frame, bg=self.colors['secondary'])
        credits_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)        
        credits_font = font.Font(family="Segoe UI", size=10, weight="normal")
        credits = tk.Label(credits_frame, 
                          text="💻 Juegos de Visión por Computadora - Simon Chumacero Espada - Junio 2025 ", 
                          font=credits_font, bg=self.colors['secondary'], 
                          fg=self.colors['text_secondary'])
        credits.pack(anchor=tk.W)
        
        # Version info
        version_label = tk.Label(credits_frame, 
                               text="v2.0 - Interfaz Mejorada", 
                               font=('Segoe UI', 8), bg=self.colors['secondary'], 
                               fg=self.colors['text_secondary'])
        version_label.pack(anchor=tk.W)
        
        # Button container
        button_frame = tk.Frame(footer_frame, bg=self.colors['secondary'])
        button_frame.pack(side=tk.RIGHT)
          # Exit button with modern styling
        exit_btn = ttk.Button(button_frame, text="❌ Salir", 
                             command=self.root.destroy, style='Small.TButton')
        exit_btn.pack()
        
    def load_cameras(self):
        """Load all available cameras and update the UI"""
        self.camera_listbox.delete(0, tk.END)
        
        # Get available cameras
        self.cameras = list_available_cameras()
        
        if not self.cameras:
            self.camera_listbox.insert(tk.END, "No se detectaron cámaras")
        else:
            for idx, cam_id in enumerate(self.cameras):
                self.camera_listbox.insert(tk.END, f"Camera {cam_id}")
            
            # Select the first camera by default
            self.camera_listbox.selection_set(0)
    
    def get_selected_camera_id(self):
        """Get the ID of the currently selected camera"""
        selection = self.camera_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Por favor selecciona una cámara")
            return None
        
        index = selection[0]
        if index >= len(self.cameras):
            messagebox.showerror("Error", "Selección de cámara inválida")
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
                    messagebox.showerror("Error", f"Script del juego no encontrado: {script_name}")
                    return
                
                # Launch the game in a separate process
                messagebox.showinfo("Lanzando Juego", message)
                
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
                messagebox.showerror("Error", f"Falló al lanzar el juego: {str(e)}")        
    def launch_arcade_1942(self):
        """Launch the Arcade 1942 game controller"""
        self.launch_game(
            "arcade_1942_mouse_controller.py", 
            "Lanzando controlador de Arcade 1942. ¡Usa gestos de manos para controlar el juego!"
        )        
    def launch_geometry_dash(self):
        """Launch the Geometry Dash game controller"""
        self.launch_game(
            "geometry_dash_hand_controller.py", 
            "Lanzando controlador de Geometry Dash. ¡Usa gestos de manos para saltar y navegar!"
        )        
    def launch_subway_surfers(self):
        """Launch the Subway Surfers game controller"""
        self.launch_game(
            "subway_surfers_pose_detection.py", 
            "Lanzando controlador de Subway Surfers. ¡Usa poses corporales para controlar el juego!"
        )

def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = ComputerVisionGamesMenu(root)
    root.mainloop()

if __name__ == "__main__":
    main()