#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Playing Arcade 1942 Game using Hand Detection

This script uses computer vision and hand detection to control the 1942 arcade game
with hand movements. It detects hand landmarks via webcam and translates them to game controls.

Requirements:
- Python 3.10
- OpenCV
- MediaPipe
- PyAutoGUI
"""

import os
import sys
import cv2
import time
import pyautogui
import numpy as np
import mediapipe as mp
import argparse

# Initialize mediapipe hands class
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Setup the Hand function for videos
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=1)  # Utilizamos solo 1 mano para control más preciso

# Disable the PyAutoGUI fail-safe
pyautogui.FAILSAFE = False

def try_available_cameras():
    """Try to find available cameras and return the index of the first one that works"""
    print("Buscando cámaras disponibles...")
    
    # Usar directamente la cámara 3 que sabemos que funciona
    print("Usando cámara con índice 3 (confirmada)")
    return 3
    
    # El código siguiente se mantiene como respaldo pero no se ejecutará
    max_cameras_to_try = 10
    for i in range(max_cameras_to_try):
        print(f"Intentando con cámara {i}...")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"¡Cámara encontrada! Índice: {i}")
                cap.release()
                return i
            cap.release()
    print("No se encontró ninguna cámara disponible.")
    return -1

def detect_hands(image, draw=True):
    """
    Detect hand landmarks in the image.
    
    Args:
        image: Input image
        draw: Whether to draw landmarks on the image
        
    Returns:
        image: Image with landmarks drawn if specified
        results: Hand detection results
    """
    # Create a copy of the input image
    output_image = image.copy()
    
    # Convert the image from BGR into RGB format
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Perform the Hand Detection
    results = hands.process(imageRGB)
    
    # Check if hands are detected and are specified to be drawn
    if results.multi_hand_landmarks and draw:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on the output image
            mp_drawing.draw_landmarks(
                output_image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
    
    return output_image, results

def get_hand_gesture(hand_landmarks, image_shape):
    """
    Determine the gesture and position of the hand.
    
    Args:
        hand_landmarks: Landmarks of detected hand
        image_shape: Shape of the input image
        
    Returns:
        position: Dictionary with hand position information and gestures
    """
    height, width, _ = image_shape
    
    # Extract relevant landmark points
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    
    # Convert normalized coordinates to pixel coordinates
    wrist_x, wrist_y = int(wrist.x * width), int(wrist.y * height)
    
    # Calculate the center of the hand using all finger tips
    x_points = [point.x for point in hand_landmarks.landmark]
    y_points = [point.y for point in hand_landmarks.landmark]
    center_x = int(np.mean(x_points) * width)
    center_y = int(np.mean(y_points) * height)
    
    # Determine if fingers are extended
    # The finger is extended if its tip is above the middle finger MCP joint
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    middle_mcp_y = middle_mcp.y * height
    
    thumb_extended = thumb_tip.y * height < wrist.y * height
    index_extended = index_tip.y * height < middle_mcp_y
    middle_extended = middle_tip.y * height < middle_mcp_y
    ring_extended = ring_tip.y * height < middle_mcp_y
    pinky_extended = pinky_tip.y * height < middle_mcp_y
    
    # Count extended fingers
    extended_fingers = sum([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended])
    
    # Determine horizontal position (left, center, right)
    x_pos = "center"
    if center_x < width * 0.4:
        x_pos = "left"
    elif center_x > width * 0.6:
        x_pos = "right"
    
    # Determine vertical position (up, center, down)
    y_pos = "center"
    if center_y < height * 0.4:
        y_pos = "up"
    elif center_y > height * 0.6:
        y_pos = "down"
    
    # Special gestures
    # Shooting gesture: index finger extended, others closed
    is_shooting = index_extended and not middle_extended and not ring_extended and not pinky_extended
    
    # Loop/Barrel roll gesture: all fingers extended
    is_barrel_roll = extended_fingers >= 4
    
    # Start gesture: thumb and pinky extended, others closed
    is_start = thumb_extended and pinky_extended and not index_extended and not middle_extended and not ring_extended
    
    # Select gesture: thumb and index extended, others closed
    is_select = thumb_extended and index_extended and not middle_extended and not ring_extended and not pinky_extended
    
    # Return position and gesture information
    return {
        "center_x": center_x,
        "center_y": center_y, 
        "x_pos": x_pos,
        "y_pos": y_pos,
        "is_shooting": is_shooting,
        "is_barrel_roll": is_barrel_roll,
        "is_start": is_start,
        "is_select": is_select,
        "extended_fingers": extended_fingers
    }

def test_hand_detection():
    """Test hand detection and gesture recognition using webcam"""
    try:
        # Try to find an available camera
        camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            return
            
        # Initialize the VideoCapture object
        camera_video = cv2.VideoCapture(camera_index)
        camera_video.set(3, 1280)
        camera_video.set(4, 960)
        
        # Create named window
        cv2.namedWindow('Hand Detection Test', cv2.WINDOW_NORMAL)
        
        print("Press ESC to exit the test")
        
        # Variables to calculate FPS
        time1 = 0
        
        while camera_video.isOpened():
            # Read a frame
            ok, frame = camera_video.read()
            
            if not ok:
                print("Error: No se pudo leer un fotograma de la cámara")
                break
            
            # Flip the frame horizontally for natural visualization
            frame = cv2.flip(frame, 1)
            
            # Get the height and width of the frame
            height, width, _ = frame.shape
            
            # Detect hands
            frame, results = detect_hands(frame)
            
            # Process hand gestures if hands are detected
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Get hand gesture information
                    hand_info = get_hand_gesture(hand_landmarks, frame.shape)
                    
                    # Display hand position and gestures
                    cv2.putText(frame, f"Position: {hand_info['x_pos']}, {hand_info['y_pos']}", 
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.putText(frame, f"Fingers extended: {hand_info['extended_fingers']}", 
                                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Show specific gestures
                    if hand_info['is_shooting']:
                        cv2.putText(frame, "Shooting! (X)", 
                                    (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    if hand_info['is_barrel_roll']:
                        cv2.putText(frame, "Barrel Roll! (Z)", 
                                    (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        
                    if hand_info['is_start']:
                        cv2.putText(frame, "Start! (Enter)", 
                                    (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        
                    if hand_info['is_select']:
                        cv2.putText(frame, "Select! (Ctrl)", 
                                    (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
            else:
                cv2.putText(frame, "No hand detected", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Calculate and display FPS
            time2 = time.time()
            if (time2 - time1) > 0:
                fps = 1.0 / (time2 - time1)
                cv2.putText(frame, f'FPS: {int(fps)}', (width - 120, 30), 
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            time1 = time2
            
            # Display the frame
            cv2.imshow('Hand Detection Test', frame)
            
            # Wait for 1ms and check if ESC is pressed
            k = cv2.waitKey(1) & 0xFF
            if k == 27:  # ESC key
                break
        
        # Release resources
        camera_video.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error during hand detection test: {e}")
        import traceback
        traceback.print_exc()

def play_game():
    """Main function to play the 1942 arcade game with hand detection"""
    try:
        # Try to find an available camera
        camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            return
            
        # Initialize the VideoCapture object
        camera_video = cv2.VideoCapture(camera_index)
        camera_video.set(3, 1280)
        camera_video.set(4, 960)
        
        # Create named window
        cv2.namedWindow('1942 Arcade Game Hand Controller', cv2.WINDOW_NORMAL)
        
        # Variables to calculate FPS
        time1 = 0
        
        # Variables for key press management
        current_keys_pressed = set()
        last_command_time = time.time()
        command_cooldown = 0.1  # 100ms cooldown between same commands for stability
        
        # Display instructions
        print("\n============== INSTRUCCIONES DE JUEGO ==============")
        print("CONTROLES:")
        print("  - Mover la mano IZQUIERDA/DERECHA/ARRIBA/ABAJO para mover el avión")
        print("  - Apuntar con DEDO ÍNDICE para DISPARAR (tecla X)")
        print("  - Todos los dedos extendidos para LOOP/BARRIL (tecla Z)")
        print("  - Pulgar y meñique extendidos para START (tecla Enter)")
        print("  - Pulgar e índice extendidos para SELECT (tecla Ctrl)")
        print("  - Presionar ESC para salir")
        print("===================================================\n")
        
        while camera_video.isOpened():
            # Read a frame
            ok, frame = camera_video.read()
            
            if not ok:
                print("Error: No se pudo leer un fotograma de la cámara")
                break
            
            # Flip the frame horizontally for natural visualization
            frame = cv2.flip(frame, 1)
            
            # Get the height and width of the frame
            height, width, _ = frame.shape
            
            # Detect hands
            frame, results = detect_hands(frame)
            
            # Set for new keys to press this frame
            new_keys_pressed = set()
            
            # Process hand gestures if hands are detected
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Get hand gesture information
                    hand_info = get_hand_gesture(hand_landmarks, frame.shape)
                    
                    # Display hand position information
                    position_text = f"Posición: {hand_info['x_pos']}, {hand_info['y_pos']}"
                    cv2.putText(frame, position_text, (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    # Handle direction commands
                    if hand_info['x_pos'] == 'left':
                        new_keys_pressed.add('left')
                        cv2.putText(frame, "⬅️ IZQUIERDA", (10, 70), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    elif hand_info['x_pos'] == 'right':
                        new_keys_pressed.add('right')
                        cv2.putText(frame, "➡️ DERECHA", (10, 70), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        
                    if hand_info['y_pos'] == 'up':
                        new_keys_pressed.add('up')
                        cv2.putText(frame, "⬆️ ARRIBA", (10, 110), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    elif hand_info['y_pos'] == 'down':
                        new_keys_pressed.add('down')
                        cv2.putText(frame, "⬇️ ABAJO", (10, 110), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    # Handle action commands
                    current_time = time.time()
                    
                    if hand_info['is_shooting']:
                        new_keys_pressed.add('x')  # Shooting key
                        cv2.putText(frame, "🔫 DISPARANDO (X)", (10, 150), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                    if hand_info['is_barrel_roll']:
                        # Only add if enough time has passed since last barrel roll
                        if 'z' not in current_keys_pressed or (current_time - last_command_time > 1.0):
                            new_keys_pressed.add('z')  # Barrel roll key
                            last_command_time = current_time
                        cv2.putText(frame, "🔄 BARRIL/LOOP (Z)", (10, 190), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                    if hand_info['is_start']:
                        if 'enter' not in current_keys_pressed or (current_time - last_command_time > 0.5):
                            new_keys_pressed.add('enter')
                            last_command_time = current_time
                        cv2.putText(frame, "▶️ START (Enter)", (10, 230), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        
                    if hand_info['is_select']:
                        if 'ctrl' not in current_keys_pressed or (current_time - last_command_time > 0.5):
                            new_keys_pressed.add('ctrl')
                            last_command_time = current_time
                        cv2.putText(frame, "⚙️ SELECT (Ctrl)", (10, 270), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                # Mostrar esquema de gestos reconocidos
                cv2.putText(frame, "📋 GESTOS:", (width - 300, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                cv2.putText(frame, "- Índice: Disparar", (width - 300, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, "- Todos dedos: Barril", (width - 300, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, "- Pulgar+Meñique: Start", (width - 300, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, "- Pulgar+Índice: Select", (width - 300, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
            else:
                cv2.putText(frame, "⚠️ No se detecta mano", (10, height - 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Process keyboard commands - release keys that are no longer pressed
            keys_to_release = current_keys_pressed - new_keys_pressed
            for key in keys_to_release:
                pyautogui.keyUp(key)
            
            # Press new keys
            keys_to_press = new_keys_pressed - current_keys_pressed
            for key in keys_to_press:
                pyautogui.keyDown(key)
            
            # Update currently pressed keys
            current_keys_pressed = new_keys_pressed
            
            # Calculate and display FPS
            time2 = time.time()
            if (time2 - time1) > 0:
                fps = 1.0 / (time2 - time1)
                cv2.putText(frame, f'FPS: {int(fps)}', (width - 120, height - 20), 
                            cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
            time1 = time2
            
            # Display the frame
            cv2.imshow('1942 Arcade Game Hand Controller', frame)
            
            # Wait for 1ms and check if ESC is pressed
            k = cv2.waitKey(1) & 0xFF
            if k == 27:  # ESC key
                break
        
        # Release all keys before exiting
        for key in current_keys_pressed:
            pyautogui.keyUp(key)
            
        # Release resources
        camera_video.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error during game play: {e}")
        import traceback
        traceback.print_exc()

def show_help():
    """Display help information about how to use this script"""
    print("""
Arcade 1942 Hand Controller
-------------------------
Este script te permite controlar el juego arcade 1942 utilizando gestos de manos
detectados por tu cámara web.

Comandos:
  --test          Probar la detección de manos y gestos
  --play          Iniciar el controlador del juego
  --help          Mostrar este mensaje de ayuda

Instrucciones:
1. Inicia el juego 1942 en tu navegador
2. Posiciónate frente a la cámara web
3. Controla el avión con los siguientes gestos:
   - Mover mano: Controla dirección del avión (izquierda/derecha/arriba/abajo)
   - Dedo índice extendido: Disparar (X)
   - Todos los dedos extendidos: Barril/Loop (Z)
   - Pulgar y meñique extendidos: Start (Enter)
   - Pulgar e índice extendidos: Select (Ctrl)
4. Presiona ESC para salir

Requisitos:
- Python 3.8+
- OpenCV
- MediaPipe
- PyAutoGUI

Ejemplo:
  python arcade_1942_hand_controller.py --play
""")

def main():
    """Main function to parse arguments and run the appropriate function"""
    parser = argparse.ArgumentParser(description='Arcade 1942 Hand Controller')
    parser.add_argument('--test', action='store_true', help='Test hand detection and gesture recognition')
    parser.add_argument('--play', action='store_true', help='Start the game controller')
    # Eliminar este argumento ya que causa conflicto con el --help incorporado de argparse
    # parser.add_argument('--help', action='store_true', help='Show help information')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Run the appropriate function
    if args.test:
        test_hand_detection()
    elif args.play:
        play_game()

if __name__ == "__main__":
    main()