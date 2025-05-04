#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Playing Arcade 1942 Game using Mouse-Like Hand Control

Este script usa visión por computadora para controlar el juego arcade 1942
con una sensibilidad similar a la de un mouse. Detecta la mano a través
de la cámara web y traduce sus movimientos a controles precisos del juego.

Requirements:
- Python 3.10
- OpenCV
- MediaPipe
- PyAutoGUI
- NumPy
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

# Initialize mediapipe hands class
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Setup the Hand function for videos - lower complexity for better performance
hands = mp_hands.Hands(
    model_complexity=0,  # Reducido para mejor rendimiento (0 = más rápido, 1 = más preciso)
    min_detection_confidence=0.5,  # Reducido para mejor detección
    min_tracking_confidence=0.5,  # Reducido para seguimiento más fluido
    max_num_hands=1)  # Una sola mano para mayor precisión

# Disable the PyAutoGUI fail-safe
pyautogui.FAILSAFE = False

# Configuración del suavizado de movimiento
SMOOTHING_FACTOR = 0.5  # Factor de suavizado entre 0 y 1 (0 = sin suavizado, 1 = suavizado máximo)
HISTORY_LENGTH = 5  # Número de posiciones históricas para el suavizado

class HandController:
    """Controlador de mano con sensibilidad tipo mouse para juegos arcade"""
    
    def __init__(self):
        """Inicializa el controlador de mano"""
        # Variables de control generales
        self.camera_index = self._find_camera()
        self.camera = None
        # Reducir resolución para mejor rendimiento
        self.frame_width = 640   # Reducido de 1280 a 640
        self.frame_height = 480  # Reducido de 960 a 480
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Variables para el control de sensibilidad
        self.prev_hand_center = None
        self.position_history = deque(maxlen=HISTORY_LENGTH)
        self.movement_threshold = 5  # Umbral mínimo para considerar movimiento intencionado
        self.sensitivity = 2.5  # Multiplicador de sensibilidad
        
        # Variables para el control de gestos
        self.current_keys_pressed = set()
        self.last_command_time = time.time()
        self.gesture_cooldowns = {
            'barrel_roll': 1.0,  # 1 segundo entre barrel rolls
            'shoot': 0.1,        # 0.1 segundos entre disparos
            'start': 0.5,        # 0.5 segundos para start/select
            'select': 0.5
        }
        
        # Variables para el cálculo de FPS
        self.prev_time = 0
        self.current_fps = 0
        
        # Zonas de control virtual para dirección
        self.dead_zone_radius = 0.15  # Zona muerta central (radio como % del ancho)
        
        # Estado actual del jugador
        self.player_x = 0.5  # Posición relativa (0-1) del jugador en X
        self.player_y = 0.5  # Posición relativa (0-1) del jugador en Y
        
    def _find_camera(self):
        """Encuentra y devuelve el índice de la primera cámara disponible"""
        print("Buscando cámaras disponibles...")
        
        # Usar directamente la cámara 3 que sabemos que funciona
        print("Usando cámara con índice 3 (confirmada)")
        return 3
    
    def initialize_camera(self):
        """Inicializa la cámara con los parámetros deseados"""
        self.camera = cv2.VideoCapture(self.camera_index)
        self.camera.set(3, self.frame_width)
        self.camera.set(4, self.frame_height)
        
        if not self.camera.isOpened():
            raise Exception("Error: No se pudo abrir la cámara")
            
        return self.camera.isOpened()
    
    def release_resources(self):
        """Libera los recursos de la cámara y cierra las ventanas"""
        # Liberar todas las teclas antes de salir
        for key in self.current_keys_pressed:
            pyautogui.keyUp(key)
            
        # Liberar cámara y cerrar ventanas
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()
    
    def detect_hands(self, image, draw=True):
        """
        Detecta las manos en la imagen.
        
        Args:
            image: Imagen de entrada
            draw: Indica si se deben dibujar los landmarks en la imagen
            
        Returns:
            output_image: Imagen con landmarks dibujados si se especifica
            results: Resultados de la detección de manos
        """
        # Crear una versión reducida de la imagen para procesar más rápido
        # Reducir la imagen a la mitad para procesamiento
        small_image = cv2.resize(image, (0, 0), fx=0.5, fy=0.5)
        
        # Convertir la imagen de BGR a RGB
        imageRGB = cv2.cvtColor(small_image, cv2.COLOR_BGR2RGB)
        
        # Realizar la detección de manos en la imagen reducida
        results = hands.process(imageRGB)
        
        # Crear copia de imagen original solo si se detectan manos y se debe dibujar
        output_image = image
        if results.multi_hand_landmarks and draw:
            output_image = image.copy()
            for hand_landmarks in results.multi_hand_landmarks:
                # Dibujar landmarks de la mano en la imagen original
                mp_drawing.draw_landmarks(
                    output_image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())
        
        return output_image, results
    
    def get_hand_info(self, hand_landmarks, image_shape):
        """
        Determina la información de la mano detectada.
        
        Args:
            hand_landmarks: Landmarks de la mano detectada
            image_shape: Dimensiones de la imagen
            
        Returns:
            hand_info: Diccionario con información de la mano y gestos
        """
        height, width, _ = image_shape
        
        # Extraer puntos de referencia relevantes
        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
        index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
        
        # Calculate the center of the hand using all finger tips and palm
        x_points = [point.x for point in hand_landmarks.landmark]
        y_points = [point.y for point in hand_landmarks.landmark]
        center_x = int(np.mean(x_points) * width)
        center_y = int(np.mean(y_points) * height)
        
        # Usar la posición del nudillo del índice como punto de referencia más estable
        pointer_x = int(index_mcp.x * width)
        pointer_y = int(index_mcp.y * height)
        
        # Determinar si los dedos están extendidos
        # Un dedo está extendido si su punta está por encima de la articulación media del dedo medio
        middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
        middle_mcp_y = middle_mcp.y * height
        
        thumb_extended = thumb_tip.y * height < wrist.y * height
        index_extended = index_tip.y * height < middle_mcp_y
        middle_extended = middle_tip.y * height < middle_mcp_y
        ring_extended = ring_tip.y * height < middle_mcp_y
        pinky_extended = pinky_tip.y * height < middle_mcp_y
        
        # Contar dedos extendidos
        extended_fingers = sum([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended])
        
        # Gestos especiales
        # Gesto de disparo: dedo índice extendido, los demás cerrados
        is_shooting = index_extended and not middle_extended and not ring_extended and not pinky_extended
        
        # Gesto de Loop/Barrel roll: todos los dedos extendidos
        is_barrel_roll = extended_fingers >= 4
        
        # Gesto de Start: pulgar y meñique extendidos, los demás cerrados
        is_start = thumb_extended and pinky_extended and not index_extended and not middle_extended and not ring_extended
        
        # Gesto de Select: pulgar e índice extendidos, los demás cerrados
        is_select = thumb_extended and index_extended and not middle_extended and not ring_extended and not pinky_extended
        
        # Devolver información de posición y gestos
        return {
            "center_x": center_x,
            "center_y": center_y,
            "pointer_x": pointer_x,
            "pointer_y": pointer_y,
            "is_shooting": is_shooting,
            "is_barrel_roll": is_barrel_roll,
            "is_start": is_start,
            "is_select": is_select,
            "extended_fingers": extended_fingers
        }
    
    def calculate_relative_movement(self, hand_info):
        """
        Calcula el movimiento relativo de la mano para simular comportamiento de mouse
        
        Args:
            hand_info: Información de la mano detectada
            
        Returns:
            delta_x, delta_y: Movimiento relativo en X e Y
        """
        current_pos = (hand_info["pointer_x"], hand_info["pointer_y"])
        
        # Almacenar la posición actual en el historial
        self.position_history.append(current_pos)
        
        # Si es la primera detección, no hay movimiento
        if self.prev_hand_center is None:
            self.prev_hand_center = current_pos
            return 0, 0
        
        # Calcular el movimiento bruto
        delta_x = current_pos[0] - self.prev_hand_center[0]
        delta_y = current_pos[1] - self.prev_hand_center[1]
        
        # Aplicar umbral para evitar pequeños movimientos involuntarios
        if abs(delta_x) < self.movement_threshold:
            delta_x = 0
        if abs(delta_y) < self.movement_threshold:
            delta_y = 0
            
        # Aplicar sensibilidad
        delta_x *= self.sensitivity
        delta_y *= self.sensitivity
        
        # Aplicar suavizado con el historial de posiciones si tenemos suficientes muestras
        if len(self.position_history) >= 3:
            # Calcular movimiento promedio de las últimas posiciones
            avg_delta_x = sum([pos[0] for pos in self.position_history][1:]) / (len(self.position_history) - 1) - self.position_history[0][0]
            avg_delta_y = sum([pos[1] for pos in self.position_history][1:]) / (len(self.position_history) - 1) - self.position_history[0][1]
            
            # Combinar el movimiento actual con el promedio usando el factor de suavizado
            delta_x = delta_x * (1 - SMOOTHING_FACTOR) + avg_delta_x * SMOOTHING_FACTOR
            delta_y = delta_y * (1 - SMOOTHING_FACTOR) + avg_delta_y * SMOOTHING_FACTOR
        
        # Actualizar la posición anterior
        self.prev_hand_center = current_pos
        
        return delta_x, delta_y
    
    def update_player_position(self, delta_x, delta_y):
        """
        Actualiza la posición virtual del jugador basado en el movimiento detectado
        
        Args:
            delta_x: Movimiento relativo en X
            delta_y: Movimiento relativo en Y
            
        Returns:
            Nuevas teclas que deben presionarse según la posición
        """
        # Escalar el movimiento relativo a un espacio normalizado (0-1)
        scale_x = 1.0 / self.frame_width
        scale_y = 1.0 / self.frame_height
        
        # Actualizar la posición del jugador (limitada entre 0 y 1)
        self.player_x = max(0, min(1, self.player_x + delta_x * scale_x))
        self.player_y = max(0, min(1, self.player_y + delta_y * scale_y))
        
        # Calcular las teclas que deben presionarse según la posición del jugador
        new_keys = set()
        
        # Controles de dirección horizontal
        if self.player_x < 0.4:
            new_keys.add('left')
        elif self.player_x > 0.6:
            new_keys.add('right')
            
        # Controles de dirección vertical
        if self.player_y < 0.4:
            new_keys.add('up')
        elif self.player_y > 0.6:
            new_keys.add('down')
            
        return new_keys
    
    def process_gestures(self, hand_info):
        """
        Procesa los gestos de la mano y devuelve las teclas correspondientes
        
        Args:
            hand_info: Información de la mano detectada
            
        Returns:
            Conjunto de teclas que deben presionarse según los gestos
        """
        new_keys = set()
        current_time = time.time()
        
        # Gesto de disparo (X)
        if hand_info['is_shooting']:
            if current_time - self.last_command_time > self.gesture_cooldowns['shoot']:
                new_keys.add('x')
                
        # Gesto de barrel roll (Z)
        if hand_info['is_barrel_roll']:
            if 'z' not in self.current_keys_pressed and (current_time - self.last_command_time > self.gesture_cooldowns['barrel_roll']):
                new_keys.add('z')
                self.last_command_time = current_time
                
        # Gesto de Start (Enter)
        if hand_info['is_start']:
            if 'enter' not in self.current_keys_pressed and (current_time - self.last_command_time > self.gesture_cooldowns['start']):
                new_keys.add('enter')
                self.last_command_time = current_time
                
        # Gesto de Select (Ctrl)
        if hand_info['is_select']:
            if 'ctrl' not in self.current_keys_pressed and (current_time - self.last_command_time > self.gesture_cooldowns['select']):
                new_keys.add('ctrl')
                self.last_command_time = current_time
                
        return new_keys
    
    def update_key_presses(self, new_keys):
        """
        Actualiza las teclas presionadas y liberadas
        
        Args:
            new_keys: Conjunto de teclas que deben estar presionadas
        """
        # Teclas que deben liberarse (estaban presionadas pero ya no)
        keys_to_release = self.current_keys_pressed - new_keys
        for key in keys_to_release:
            pyautogui.keyUp(key)
        
        # Teclas que deben presionarse (no estaban presionadas pero ahora sí)
        keys_to_press = new_keys - self.current_keys_pressed
        for key in keys_to_press:
            pyautogui.keyDown(key)
        
        # Actualizar el conjunto de teclas presionadas
        self.current_keys_pressed = new_keys
    
    def calculate_fps(self):
        """Calcula y devuelve los FPS actuales"""
        current_time = time.time()
        if (current_time - self.prev_time) > 0:
            self.current_fps = 1.0 / (current_time - self.prev_time)
        self.prev_time = current_time
        return int(self.current_fps)
    
    def display_interface(self, frame, hand_info=None, delta_movement=None):
        """
        Muestra la interfaz del controlador en el marco de video
        
        Args:
            frame: Imagen del marco actual
            hand_info: Información de la mano detectada (None si no hay mano)
            delta_movement: Movimiento relativo calculado (dx, dy)
        """
        height, width, _ = frame.shape
        
        # Mostrar FPS
        fps = self.calculate_fps()
        cv2.putText(frame, f'FPS: {fps}', (width - 120, 30), 
                    cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
        
        # Mostrar posición virtual del jugador
        player_x_pixel = int(self.player_x * width)
        player_y_pixel = int(self.player_y * height)
        
        # Dibujar cursor virtual del jugador
        radius = 20
        # Círculo exterior (contorno blanco)
        cv2.circle(frame, (player_x_pixel, player_y_pixel), radius + 2, (255, 255, 255), 2)
        # Círculo interior (relleno verde semi-transparente)
        overlay = frame.copy()
        cv2.circle(overlay, (player_x_pixel, player_y_pixel), radius, (0, 255, 0), -1)
        # Aplicar transparencia al círculo relleno
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Mostrar zona central "muerta"
        dead_zone_radius = int(self.dead_zone_radius * width)
        center_x, center_y = width // 2, height // 2
        cv2.circle(frame, (center_x, center_y), dead_zone_radius, (100, 100, 100), 1)
        
        # Si tenemos información de la mano
        if hand_info is not None:
            # Mostrar información de posición de la mano
            cv2.putText(frame, f"Posición jugador: {self.player_x:.2f}, {self.player_y:.2f}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            if delta_movement:
                dx, dy = delta_movement
                cv2.putText(frame, f"Movimiento: {dx:.1f}, {dy:.1f}", 
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            # Mostrar teclas activas
            active_keys = []
            if 'left' in self.current_keys_pressed:
                active_keys.append("⬅️")
            if 'right' in self.current_keys_pressed:
                active_keys.append("➡️")
            if 'up' in self.current_keys_pressed:
                active_keys.append("⬆️")
            if 'down' in self.current_keys_pressed:
                active_keys.append("⬇️")
                
            if active_keys:
                cv2.putText(frame, "Dirección: " + " ".join(active_keys), 
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Mostrar acciones especiales
            if hand_info['is_shooting']:
                cv2.putText(frame, "🔫 DISPARANDO (X)", (10, 120), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            if hand_info['is_barrel_roll']:
                cv2.putText(frame, "🔄 BARRIL/LOOP (Z)", (10, 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
            if hand_info['is_start']:
                cv2.putText(frame, "▶️ START (Enter)", (10, 180), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
            if hand_info['is_select']:
                cv2.putText(frame, "⚙️ SELECT (Ctrl)", (10, 210), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
        else:
            cv2.putText(frame, "⚠️ No se detecta mano", (10, height - 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        # Mostrar guía de gestos
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
            
    def test_detection(self):
        """Prueba la detección de manos y muestra la interfaz de prueba"""
        try:
            if not self.initialize_camera():
                return
                
            cv2.namedWindow('Mouse-Like Hand Detection Test', cv2.WINDOW_NORMAL)
            print("Presiona ESC para salir de la prueba")
            
            while self.camera.isOpened():
                # Leer un fotograma
                ok, frame = self.camera.read()
                
                if not ok:
                    print("Error: No se pudo leer un fotograma de la cámara")
                    break
                
                # Voltear horizontalmente para una visualización natural
                frame = cv2.flip(frame, 1)
                
                # Detectar manos
                frame, results = self.detect_hands(frame)
                
                # Variables para el movimiento relativo
                delta_x, delta_y = 0, 0
                hand_info = None
                
                # Procesar gestos si se detectan manos
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Obtener información de la mano
                        hand_info = self.get_hand_info(hand_landmarks, frame.shape)
                        
                        # Calcular movimiento relativo
                        delta_x, delta_y = self.calculate_relative_movement(hand_info)
                        
                        # Actualizar posición del jugador y obtener nuevas teclas a presionar
                        movement_keys = self.update_player_position(delta_x, delta_y)
                        
                        # Obtener teclas de gestos
                        gesture_keys = self.process_gestures(hand_info)
                        
                        # Combinar todas las teclas
                        new_keys = movement_keys.union(gesture_keys)
                        
                        # Actualizar teclas presionadas
                        self.update_key_presses(new_keys)
                else:
                    # No hay manos detectadas, restablecer todo
                    self.prev_hand_center = None
                    self.update_key_presses(set())
                
                # Mostrar la interfaz
                self.display_interface(frame, hand_info, (delta_x, delta_y))
                
                # Mostrar el fotograma
                cv2.imshow('Mouse-Like Hand Detection Test', frame)
                
                # Esperar 1ms y verificar si se presiona ESC
                k = cv2.waitKey(1) & 0xFF
                if k == 27:  # Tecla ESC
                    break
            
            self.release_resources()
            
        except Exception as e:
            print(f"Error durante la prueba de detección: {e}")
            import traceback
            traceback.print_exc()
            self.release_resources()
    
    def play_game(self):
        """Función principal para jugar al juego arcade 1942 con detección de manos"""
        try:
            if not self.initialize_camera():
                return
                
            cv2.namedWindow('1942 Arcade Mouse-Like Controller', cv2.WINDOW_NORMAL)
            
            # Mostrar instrucciones
            print("\n============== INSTRUCCIONES DE JUEGO ==============")
            print("CONTROLES:")
            print("  - Mover la mano como un mouse para controlar el avión")
            print("  - Dedo índice extendido para DISPARAR (tecla X)")
            print("  - Todos los dedos extendidos para LOOP/BARRIL (tecla Z)")
            print("  - Pulgar y meñique extendidos para START (tecla Enter)")
            print("  - Pulgar e índice extendidos para SELECT (tecla Ctrl)")
            print("  - Presionar ESC para salir")
            print("\nAJUSTES DE SENSIBILIDAD:")
            print("  - Detecta y sigue el movimiento relativo de la mano")
            print("  - Comportamiento similar al de un mouse")
            print("  - Suavizado de movimiento para mayor precisión")
            print("===================================================\n")
            
            # Posicionar al jugador en el centro al inicio
            self.player_x = 0.5
            self.player_y = 0.5
            
            while self.camera.isOpened():
                # Leer un fotograma
                ok, frame = self.camera.read()
                
                if not ok:
                    print("Error: No se pudo leer un fotograma de la cámara")
                    break
                
                # Voltear horizontalmente para una visualización natural
                frame = cv2.flip(frame, 1)
                
                # Detectar manos
                frame, results = self.detect_hands(frame)
                
                # Variables para el movimiento relativo
                delta_x, delta_y = 0, 0
                hand_info = None
                
                # Procesar gestos si se detectan manos
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Obtener información de la mano
                        hand_info = self.get_hand_info(hand_landmarks, frame.shape)
                        
                        # Calcular movimiento relativo
                        delta_x, delta_y = self.calculate_relative_movement(hand_info)
                        
                        # Actualizar posición del jugador y obtener nuevas teclas a presionar
                        movement_keys = self.update_player_position(delta_x, delta_y)
                        
                        # Obtener teclas de gestos
                        gesture_keys = self.process_gestures(hand_info)
                        
                        # Combinar todas las teclas
                        new_keys = movement_keys.union(gesture_keys)
                        
                        # Actualizar teclas presionadas
                        self.update_key_presses(new_keys)
                else:
                    # No hay manos detectadas, restablecer todo excepto la posición virtual del jugador
                    self.prev_hand_center = None
                    # Liberar todas las teclas pero mantener la posición virtual
                    self.update_key_presses(set())
                
                # Mostrar la interfaz
                self.display_interface(frame, hand_info, (delta_x, delta_y))
                
                # Mostrar el fotograma
                cv2.imshow('1942 Arcade Mouse-Like Controller', frame)
                
                # Esperar 1ms y verificar si se presiona ESC
                k = cv2.waitKey(1) & 0xFF
                if k == 27:  # Tecla ESC
                    break
            
            self.release_resources()
            
        except Exception as e:
            print(f"Error durante el juego: {e}")
            import traceback
            traceback.print_exc()
            self.release_resources()
    
    def adjust_sensitivity(self, new_sensitivity):
        """Ajusta la sensibilidad del controlador"""
        self.sensitivity = max(0.5, min(5.0, new_sensitivity))
        print(f"Sensibilidad ajustada a: {self.sensitivity}")
    
    def adjust_smoothing(self, new_smoothing):
        """Ajusta el factor de suavizado del controlador"""
        global SMOOTHING_FACTOR
        SMOOTHING_FACTOR = max(0.0, min(1.0, new_smoothing))
        print(f"Factor de suavizado ajustado a: {SMOOTHING_FACTOR}")

def show_help():
    """Muestra información de ayuda sobre cómo usar este script"""
    print("""
Arcade 1942 Mouse-Like Controller
-------------------------------
Este script te permite controlar el juego arcade 1942 utilizando gestos de manos
detectados por tu cámara web, con una sensibilidad similar a la de un mouse.

Comandos:
  --test              Probar la detección de manos y gestos
  --play              Iniciar el controlador del juego
  --sensitivity=N     Ajustar sensibilidad (0.5-5.0, por defecto 2.5)
  --smoothing=N       Ajustar suavizado (0.0-1.0, por defecto 0.5)
  --help              Mostrar este mensaje de ayuda

Características:
- Control de sensibilidad tipo mouse (movimiento relativo)
- Suavizado de movimientos para mayor precisión
- Detección precisa de gestos
- Interfaz visual intuitiva

Instrucciones:
1. Inicia el juego 1942 en tu navegador
2. Posiciónate frente a la cámara web
3. Controla el avión con los siguientes gestos:
   - Mover mano: Control preciso del avión (como un mouse)
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
- NumPy

Ejemplo:
  python arcade_1942_mouse_controller.py --play --sensitivity=2.0 --smoothing=0.7
""")

def main():
    """Función principal para analizar argumentos y ejecutar la función apropiada"""
    parser = argparse.ArgumentParser(description='Arcade 1942 Mouse-Like Controller')
    parser.add_argument('--test', action='store_true', help='Probar detección de manos y gestos')
    parser.add_argument('--play', action='store_true', help='Iniciar el controlador del juego')
    parser.add_argument('--sensitivity', type=float, default=2.5, 
                        help='Ajustar sensibilidad (0.5-5.0, por defecto 2.5)')
    parser.add_argument('--smoothing', type=float, default=0.5, 
                        help='Ajustar suavizado (0.0-1.0, por defecto 0.5)')
    
    # Analizar argumentos
    args = parser.parse_args()
    
    # Mostrar ayuda si no se proporcionan argumentos
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Inicializar controlador
    controller = HandController()
    
    # Ajustar sensibilidad y suavizado si se especifican
    controller.adjust_sensitivity(args.sensitivity)
    controller.adjust_smoothing(args.smoothing)
    
    # Ejecutar la función apropiada
    if args.test:
        controller.test_detection()
    elif args.play:
        controller.play_game()

if __name__ == "__main__":
    main()