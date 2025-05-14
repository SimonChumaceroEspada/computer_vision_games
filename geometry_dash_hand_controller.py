#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Playing Geometry Dash Game using Hand Detection

Este script utiliza visión por computadora y detección de manos para controlar el juego 
Geometry Dash mediante gestos. Detecta gestos de manos a través de la webcam y los traduce 
a controles del juego con un tiempo de respuesta mínimo.

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
from collections import deque

# Configuración para máxima velocidad de respuesta
pyautogui.PAUSE = 0.0  # Eliminar el retraso entre comandos de PyAutoGUI
pyautogui.FAILSAFE = False  # Desactivar el fail-safe de PyAutoGUI

# Inicializar MediaPipe Hands con configuración de bajo procesamiento
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Configurar MediaPipe Hands para máxima velocidad
# model_complexity=0: modelo más rápido (menos preciso pero suficiente)
# min_detection_confidence: valor bajo para detectar siempre la mano
hands = mp_hands.Hands(
    static_image_mode=False,
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=1)  # Solo necesitamos una mano para mayor rendimiento

# Historial para suavizado de gestos (evita falsos positivos)
GESTURE_HISTORY_LENGTH = 3  # Pequeño para mantener la velocidad pero filtrar ruido
DEBOUNCE_TIME = 0.05  # 50ms de debounce para evitar múltiples activaciones

def try_available_cameras():
    """Intenta encontrar cámaras disponibles y devuelve el índice de la primera que funciona"""
    print("Buscando cámaras disponibles...")
    
    # Usar directamente la cámara 3 que sabemos que funciona
    print("Usando cámara con índice 3 (confirmada)")
    return 3
    
    # Código de respaldo que no se ejecutará
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

def process_frame(frame):
    """Preprocesa el frame para acelerar la detección de manos"""
    # Reducir el tamaño del frame para acelerar el procesamiento
    # Reducimos a la mitad para un buen balance entre velocidad y precisión
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    
    # Convertir a RGB (requerido por MediaPipe)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    return rgb_frame

def detect_hand_landmarks(frame):
    """
    Detecta los landmarks de la mano en el frame.
    
    Args:
        frame: Frame procesado (RGB)
        
    Returns:
        results: Resultados de la detección de manos
    """
    # Procesar el frame con MediaPipe Hands (con escritura desactivada para máxima velocidad)
    results = hands.process(frame)
    
    return results

def detect_hand_gesture(results, frame_shape):
    """
    Detecta gestos específicos de la mano para controlar Geometry Dash.
    
    Args:
        results: Resultados de la detección de manos
        frame_shape: Dimensiones del frame
        
    Returns:
        gesture: Gesto detectado ('jump', 'none')
        hand_closed: Si la mano está cerrada o no
        landmarks_px: Landmarks de la mano en píxeles (si se detectaron)
    """
    height, width = frame_shape[:2]
    scale_factor = 2.0  # Factor para compensar el frame redimensionado
    
    if not results.multi_hand_landmarks:
        return 'none', False, None
    
    # Solo procesamos la primera mano detectada
    hand_landmarks = results.multi_hand_landmarks[0]
    
    # Convertir landmarks normalizados a coordenadas en píxeles
    landmarks_px = []
    for landmark in hand_landmarks.landmark:
        x = int(landmark.x * width * scale_factor)
        y = int(landmark.y * height * scale_factor)
        landmarks_px.append((x, y))
    
    # Extraer landmarks específicos para gestos
    thumb_tip = landmarks_px[4]     # Punta del pulgar
    index_tip = landmarks_px[8]     # Punta del índice
    middle_tip = landmarks_px[12]   # Punta del medio
    ring_tip = landmarks_px[16]     # Punta del anular
    pinky_tip = landmarks_px[20]    # Punta del meñique
    
    # Calcular distancia entre pulgar e índice para detectar pellizco
    thumb_index_distance = calculate_distance(thumb_tip, index_tip)
    
    # Verificar si los dedos están extendidos
    finger_tips = [index_tip, middle_tip, ring_tip, pinky_tip]
    finger_bases = [landmarks_px[5], landmarks_px[9], landmarks_px[13], landmarks_px[17]]  # Base de cada dedo
    
    fingers_extended = []
    for i, (tip, base) in enumerate(zip(finger_tips, finger_bases)):
        # Un dedo está extendido si su punta está por encima (Y menor) que su base
        if tip[1] < base[1] - 30:  # Añadir un umbral de 30px para mayor robustez
            fingers_extended.append(True)
        else:
            fingers_extended.append(False)
    
    # Añadir estado del pulgar (el pulgar está extendido si su X es menor que la base del índice para mano derecha)
    thumb_extended = False
    if thumb_tip[0] < landmarks_px[5][0] - 20:  # Base del índice - umbral
        thumb_extended = True
    
    fingers_extended.insert(0, thumb_extended)
    
    # Contar dedos extendidos
    extended_count = sum(fingers_extended)
    
    # Determinar si la mano está cerrada
    hand_closed = extended_count <= 1
    
    # SALTO: Pellizco (pulgar e índice juntos)
    # La distancia entre la punta del pulgar y la punta del índice debe ser muy pequeña
    # Umbral reducido a 30 píxeles (era 50) para requerir que estén más juntos
    if thumb_index_distance < 30:
        return 'jump', hand_closed, landmarks_px
    
    # Sin gesto específico
    return 'none', hand_closed, landmarks_px

def calculate_distance(point1, point2):
    """Calcula la distancia euclidiana entre dos puntos"""
    return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def draw_hand_landmarks(frame, landmarks_px, gesture):
    """
    Dibuja los landmarks de la mano y el gesto detectado en el frame.
    
    Args:
        frame: Frame de video
        landmarks_px: Landmarks de la mano en píxeles
        gesture: Gesto detectado
    
    Returns:
        frame: Frame con los landmarks y el gesto dibujados
    """
    if landmarks_px is None:
        return frame
    
    # Crear una copia del frame para dibujar
    output_frame = frame.copy()
    
    # Dibujar círculos en cada landmark
    for i, (x, y) in enumerate(landmarks_px):
        # Puntas de los dedos en verde más grande
        if i in [4, 8, 12, 16, 20]:
            cv2.circle(output_frame, (x, y), 8, (0, 255, 0), -1)
        # Resto de landmarks en azul más pequeño
        else:
            cv2.circle(output_frame, (x, y), 5, (255, 0, 0), -1)
    
    # Dibujar conexiones entre landmarks para visualizar la mano
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),  # Pulgar
        (0, 5), (5, 6), (6, 7), (7, 8),  # Índice
        (5, 9), (9, 10), (10, 11), (11, 12),  # Medio
        (9, 13), (13, 14), (14, 15), (15, 16),  # Anular
        (13, 17), (17, 18), (18, 19), (19, 20),  # Meñique
        (0, 17), (5, 9), (9, 13), (13, 17)  # Palma
    ]
    
    for connection in connections:
        cv2.line(output_frame, landmarks_px[connection[0]], landmarks_px[connection[1]], 
                 (0, 255, 255), 2)
    
    # Dibujar texto indicando el gesto
    if gesture == 'jump':
        cv2.putText(output_frame, "JUMP!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, 
                    (0, 255, 0), 3)
    
    return output_frame

def play_geometry_dash(camera_index=None):
    """Función principal para jugar Geometry Dash con detección de manos"""
    try:
        # Encontrar una cámara disponible
        if camera_index is None:
            camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            return
        
        # Inicializar la cámara con resolución reducida para mayor velocidad
        camera = cv2.VideoCapture(camera_index)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Ancho reducido
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Alto reducido
        camera.set(cv2.CAP_PROP_FPS, 60)  # Intentar mayor FPS si la cámara lo soporta
        
        if not camera.isOpened():
            print(f"Error: No se pudo abrir la cámara con índice {camera_index}")
            return
        
        # Crear ventana
        cv2.namedWindow('Geometry Dash Hand Controller', cv2.WINDOW_NORMAL)
        
        # Variables para seguimiento de tiempo y FPS
        prev_time = time.time()
        fps_history = deque(maxlen=10)
        
        # Variables para el control de gestos y teclas
        gesture_history = deque(['none'] * GESTURE_HISTORY_LENGTH, maxlen=GESTURE_HISTORY_LENGTH)
        last_jump_time = 0
        jump_active = False
        
        # Mostrar instrucciones
        print("\n============== GEOMETRY DASH HAND CONTROLLER ==============")
        print("CONTROLES SIMPLIFICADOS:")
        print("  - SALTAR (Espacio): Pellizco/pinza con pulgar e índice juntos")
        print("  - Presionar ESC en la ventana para salir")
        print("==========================================================\n")
        
        # Bucle principal
        while camera.isOpened():
            # Capturar frame
            success, frame = camera.read()
            if not success:
                print("Error al leer frame de la cámara")
                break
            
            # Voltear horizontalmente para visualización natural
            frame = cv2.flip(frame, 1)
            
            # Calcular FPS
            current_time = time.time()
            fps = 1 / (current_time - prev_time)
            fps_history.append(fps)
            avg_fps = sum(fps_history) / len(fps_history)
            prev_time = current_time
            
            # Preprocesar frame para detección más rápida
            processed_frame = process_frame(frame)
            
            # Detectar landmarks de la mano
            results = detect_hand_landmarks(processed_frame)
            
            # Detectar gestos de la mano
            gesture, hand_closed, landmarks_px = detect_hand_gesture(results, processed_frame.shape)
            
            # Actualizar historial de gestos
            gesture_history.append(gesture)
            
            # Ejecutar acciones basadas en gestos
            # Solo ejecutamos si el mismo gesto se detecta consistentemente
            if gesture_history.count('jump') >= GESTURE_HISTORY_LENGTH - 1:
                current_time = time.time()
                # Verificar debounce para evitar múltiples activaciones
                if current_time - last_jump_time > DEBOUNCE_TIME and not jump_active:
                    # Presionar espacio para saltar
                    pyautogui.keyDown('space')
                    jump_active = True
                    last_jump_time = current_time
            elif jump_active:
                # Soltar tecla de espacio cuando no se detecta gesto de salto
                pyautogui.keyUp('space')
                jump_active = False
            
            # Dibujar landmarks y gestos en el frame
            if landmarks_px is not None:
                frame = draw_hand_landmarks(frame, landmarks_px, gesture)
            
            # Mostrar FPS en el frame
            cv2.putText(frame, f"FPS: {int(avg_fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                        1, (0, 255, 0), 2)
            
            # Mostrar estado actual
            if gesture == 'jump':
                cv2.putText(frame, "Acción: SALTAR (Espacio)", (10, frame.shape[0] - 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            
            # Mostrar instrucciones en pantalla
            cv2.putText(frame, "Pellizco (pulgar e índice): Saltar", (frame.shape[1] - 280, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostrar estado de la mano
            if landmarks_px is None:
                cv2.putText(frame, "Estado: No se detecta mano", (10, frame.shape[0] - 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, f"Estado: Mano {'cerrada' if hand_closed else 'abierta'}", 
                            (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mostrar frame
            cv2.imshow('Geometry Dash Hand Controller', frame)
            
            # Salir con ESC
            if cv2.waitKey(1) & 0xFF == 27:
                break
        
        # Asegurar que se sueltan todas las teclas
        pyautogui.keyUp('space')
        
        # Liberar recursos
        camera.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Asegurar que se sueltan todas las teclas
        pyautogui.keyUp('space')

def test_hand_detection(camera_index=None):
    """Función para probar la detección de manos y gestos sin controlar el juego"""
    try:
        # Encontrar una cámara disponible
        if camera_index is None:
            camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            return
        
        # Inicializar la cámara
        camera = cv2.VideoCapture(camera_index)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not camera.isOpened():
            print(f"Error: No se pudo abrir la cámara con índice {camera_index}")
            return
        
        # Crear ventana
        cv2.namedWindow('Hand Gesture Test', cv2.WINDOW_NORMAL)
        
        # Variables para seguimiento de tiempo y FPS
        prev_time = time.time()
        
        print("\n============== TEST DE DETECCIÓN DE GESTOS ==============")
        print("Prueba los gestos ACTUALIZADOS:")
        print("  - SALTAR (Espacio): Pellizco con pulgar e índice juntos")
        print("  - Presionar ESC en la ventana para salir")
        print("=======================================================\n")
        
        # Bucle principal
        while camera.isOpened():
            # Capturar frame
            success, frame = camera.read()
            if not success:
                print("Error al leer frame de la cámara")
                break
            
            # Voltear horizontalmente para visualización natural
            frame = cv2.flip(frame, 1)
            
            # Calcular FPS
            current_time = time.time()
            fps = 1 / (current_time - prev_time)
            prev_time = current_time
            
            # Preprocesar frame para detección más rápida
            processed_frame = process_frame(frame)
            
            # Detectar landmarks de la mano
            results = detect_hand_landmarks(processed_frame)
            
            # Detectar gestos de la mano
            gesture, hand_closed, landmarks_px = detect_hand_gesture(results, processed_frame.shape)
            
            # Dibujar landmarks y gestos en el frame
            if landmarks_px is not None:
                frame = draw_hand_landmarks(frame, landmarks_px, gesture)
            
            # Mostrar FPS en el frame
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Mostrar gesto detectado
            cv2.putText(frame, f"Gesto: {gesture.upper()}", (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # Mostrar instrucciones en pantalla
            cv2.putText(frame, "Pellizco (pulgar e índice): Saltar", (frame.shape[1] - 280, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostrar frame
            cv2.imshow('Hand Gesture Test', frame)
            
            # Salir con ESC
            if cv2.waitKey(1) & 0xFF == 27:
                break
        
        # Liberar recursos
        camera.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def show_help():
    """Muestra información de ayuda sobre cómo usar este script"""
    print("""
Geometry Dash Hand Controller
-----------------------------
Este script te permite jugar Geometry Dash usando gestos de mano
detectados por tu cámara web.

Comandos:
  --test          Probar la detección de gestos de mano
  --play          Iniciar el controlador del juego
  --help          Mostrar este mensaje de ayuda

Instrucciones:
1. Abre el juego Geometry Dash
2. Ejecuta este script con la opción --play
3. Usa el siguiente gesto para controlar el juego:
   - Pellizco (pulgar e índice juntos): SALTAR (Espacio)
4. Presiona ESC para salir

Requisitos:
- Python 3.8+
- OpenCV
- MediaPipe
- PyAutoGUI

Ejemplo:
  python geometry_dash_hand_controller.py --play
""")

def main():
    """Función principal que analiza argumentos y ejecuta la función correspondiente"""
    parser = argparse.ArgumentParser(description='Geometry Dash Hand Controller')
    parser.add_argument('--test', action='store_true', help='Probar la detección de gestos de mano')
    parser.add_argument('--play', action='store_true', help='Iniciar el controlador del juego')
    parser.add_argument('--camera', type=int, help='Índice de la cámara a utilizar')
    
    # Analizar argumentos
    args = parser.parse_args()
    
    # Mostrar ayuda si no se proporcionan argumentos
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Ejecutar la función correspondiente
    if args.test:
        test_hand_detection(camera_index=args.camera)
    elif args.play:
        play_geometry_dash(camera_index=args.camera)

if __name__ == "__main__":
    main()