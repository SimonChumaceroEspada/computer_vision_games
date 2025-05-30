#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test simple para verificar la detección del gesto de barril roll
"""

import cv2
import time
import mediapipe as mp
import numpy as np

# Initialize mediapipe hands class
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Setup the Hand function for videos
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=1)

def detect_barrel_roll_gesture(hand_landmarks):
    """
    Detecta específicamente el gesto de barril roll (solo dedo índice extendido)
    """
    # Extraer puntos de referencia relevantes
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    
    # Puntos MCP (articulaciones)
    thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]
    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
    ring_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP]
    pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
    
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
    
    # Determinar si los dedos están extendidos
    # Para el pulgar, comparar con el MCP del pulgar (orientación diferente)
    thumb_extended = thumb_tip.x > thumb_mcp.x if thumb_tip.x > wrist.x else thumb_tip.x < thumb_mcp.x
    
    # Para los otros dedos, comparar la punta con su respectivo MCP
    index_extended = index_tip.y < index_mcp.y
    middle_extended = middle_tip.y < middle_mcp.y
    ring_extended = ring_tip.y < ring_mcp.y
    pinky_extended = pinky_tip.y < pinky_mcp.y
    
    # Gesto de Barril/Loop (X): SOLO el dedo índice extendido, todos los demás cerrados
    is_barrel_roll = (index_extended and 
                     not thumb_extended and 
                     not middle_extended and 
                     not ring_extended and 
                     not pinky_extended)
    
    return {
        'is_barrel_roll': is_barrel_roll,
        'thumb_extended': thumb_extended,
        'index_extended': index_extended,
        'middle_extended': middle_extended,
        'ring_extended': ring_extended,
        'pinky_extended': pinky_extended
    }

def main():
    """Función principal de prueba"""
    # Inicializar cámara
    camera = cv2.VideoCapture(3)  # Usar cámara 3
    camera.set(3, 640)  # Ancho
    camera.set(4, 480)  # Alto
    
    if not camera.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    print("=== PRUEBA DE DETECCIÓN DE BARRIL ROLL ===")
    print("Extiende SOLO el dedo índice para activar el barril roll")
    print("Presiona ESC para salir")
    
    last_barrel_time = 0
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
            
        # Voltear horizontalmente
        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape
        
        # Convertir a RGB para MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        # Si se detectan manos
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Dibujar landmarks
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())
                
                # Detectar gesto
                gesture_info = detect_barrel_roll_gesture(hand_landmarks)
                
                # Mostrar información de debug
                y_offset = 30
                finger_names = ["Pulgar", "Índice", "Medio", "Anular", "Meñique"]
                finger_states = [
                    gesture_info['thumb_extended'],
                    gesture_info['index_extended'],
                    gesture_info['middle_extended'],
                    gesture_info['ring_extended'],
                    gesture_info['pinky_extended']
                ]
                
                for i, (name, state) in enumerate(zip(finger_names, finger_states)):
                    color = (0, 255, 0) if state else (0, 0, 255)
                    status = "✓" if state else "✗"
                    cv2.putText(frame, f"{name}: {status}", (10, y_offset + i*25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Mostrar estado del barril roll
                if gesture_info['is_barrel_roll']:
                    current_time = time.time()
                    if current_time - last_barrel_time > 0.5:  # Cooldown de 0.5 segundos
                        cv2.putText(frame, "🔄 BARRIL ROLL DETECTADO!", (10, height - 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                        print(f"⚡ BARRIL ROLL! Tiempo: {current_time:.2f}")
                        last_barrel_time = current_time
                    else:
                        cv2.putText(frame, "🔄 BARRIL ROLL (Cooldown)", (10, height - 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)
                else:
                    cv2.putText(frame, "Levanta SOLO el índice", (10, height - 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        else:
            cv2.putText(frame, "⚠️ No se detecta mano", (10, height - 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Mostrar frame
        cv2.imshow('Test Barrel Roll', frame)
        
        # Salir con ESC
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    # Limpiar
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
