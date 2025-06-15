#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Playing Subway Surfers Game using Pose Detection

This script uses computer vision and pose detection to control the Subway Surfers game
with body movements. It detects body poses via webcam and translates them to game controls.

Requirements:
- Python 3.10
- OpenCV
- MediaPipe
- PyAutoGUI
- Matplotlib
"""

import os
import sys
import cv2
import pyautogui
from time import time
from math import hypot
import mediapipe as mp
import matplotlib.pyplot as plt
import argparse
import webbrowser

# Initialize mediapipe pose class
mp_pose = mp.solutions.pose

# Setup the Pose function for images and videos
pose_image = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5, model_complexity=1)
pose_video = mp_pose.Pose(static_image_mode=False, model_complexity=1, min_detection_confidence=0.7,
                         min_tracking_confidence=0.7)

# Initialize mediapipe drawing class
mp_drawing = mp.solutions.drawing_utils

def detectPose(image, pose, draw=False, display=False):
    '''
    This function performs the pose detection on the most prominent person in an image.
    Args:
        image:   The input image with a prominent person whose pose landmarks needs to be detected.
        pose:    The pose function required to perform the pose detection.
        draw:    A boolean value that is if set to true the function draw pose landmarks on the output image. 
        display: A boolean value that is if set to true the function displays the original input image, and the 
                 resultant image and returns nothing.
    Returns:
        output_image: The input image with the detected pose landmarks drawn if it was specified.
        results:      The output of the pose landmarks detection on the input image.
    '''
    
    # Create a copy of the input image
    output_image = image.copy()
    
    # Convert the image from BGR into RGB format
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Perform the Pose Detection
    results = pose.process(imageRGB)
    
    # Check if any landmarks are detected and are specified to be drawn
    if results.pose_landmarks and draw:
    
        # Draw Pose Landmarks on the output image
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks,
                                  connections=mp_pose.POSE_CONNECTIONS,
                                  landmark_drawing_spec=mp_drawing.DrawingSpec(color=(255,255,255),
                                                                               thickness=3, circle_radius=3),
                                  connection_drawing_spec=mp_drawing.DrawingSpec(color=(49,125,237),
                                                                               thickness=2, circle_radius=2))

    # Check if the original input image and the resultant image are specified to be displayed
    if display:
    
        # Display the original input image and the resultant image
        plt.figure(figsize=[22,22])
        plt.subplot(121);plt.imshow(image[:,:,::-1]);plt.title("Original Image");plt.axis('off');
        plt.subplot(122);plt.imshow(output_image[:,:,::-1]);plt.title("Output Image");plt.axis('off');
        plt.show()
        
    # Otherwise
    else:
        # Return the output image and the results of pose landmarks detection
        return output_image, results

def checkHandsJoined(image, results, draw=False, display=False):
    '''
    This function checks whether the hands of the person are joined or not in an image.
    Args:
        image:   The input image with a prominent person whose hands status (joined or not) needs to be classified.
        results: The output of the pose landmarks detection on the input image.
        draw:    A boolean value that is if set to true the function writes the hands status & distance on the output image. 
        display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
    Returns:
        output_image: The same input image but with the classified hands status written, if it was specified.
        hand_status:  The classified status of the hands whether they are joined or not.
    '''
    
    # Get the height and width of the input image.
    height, width, _ = image.shape
    
    # Create a copy of the input image to write the hands status label on.
    output_image = image.copy()
    
    # Get the left wrist landmark x and y coordinates.
    left_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].x * width,
                          results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].y * height)

    # Get the right wrist landmark x and y coordinates.
    right_wrist_landmark = (results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].x * width,
                           results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].y * height)
    
    # Calculate the euclidean distance between the left and right wrist.
    euclidean_distance = int(hypot(left_wrist_landmark[0] - right_wrist_landmark[0],
                                   left_wrist_landmark[1] - right_wrist_landmark[1]))
    
    # Compare the distance between the wrists with a appropriate threshold to check if both hands are joined.
    # Aumentamos el umbral para que sea más fácil detectar las manos unidas
    if euclidean_distance < 180:  # Valor original: 130
        
        # Set the hands status to joined.
        hand_status = 'Hands Joined'
        
        # Set the color value to green.
        color = (0, 255, 0)
        
    # Otherwise.    
    else:
        
        # Set the hands status to not joined.
        hand_status = 'Hands Not Joined'
        
        # Set the color value to red.
        color = (0, 0, 255)
        
    # Check if the Hands Joined status and hands distance are specified to be written on the output image.
    if draw:

        # Write the classified hands status on the image. 
        cv2.putText(output_image, hand_status, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, color, 3)
        
        # Write the the distance between the wrists on the image. 
        cv2.putText(output_image, f'Distance: {euclidean_distance}', (10, 70),
                    cv2.FONT_HERSHEY_PLAIN, 2, color, 3)
        
    # Check if the output image is specified to be displayed.
    if display:

        # Display the output image.
        plt.figure(figsize=[10,10])
        plt.imshow(output_image[:,:,::-1]);plt.title("Output Image");plt.axis('off');
        plt.show()
    
    # Otherwise
    else:
    
        # Return the output image and the classified hands status indicating whether the hands are joined or not.
        return output_image, hand_status

def checkLeftRight(image, results, draw=False, display=False):
    '''
    This function finds the horizontal position (left, center, right) of the person in an image.
    Args:
        image:   The input image with a prominent person whose the horizontal position needs to be found.
        results: The output of the pose landmarks detection on the input image.
        draw:    A boolean value that is if set to true the function writes the horizontal position on the output image. 
        display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
    Returns:
        output_image:         The same input image but with the horizontal position written, if it was specified.
        horizontal_position:  The horizontal position (left, center, right) of the person in the input image.
    '''
    
    # Declare a variable to store the horizontal position (left, center, right) of the person.
    horizontal_position = None
    
    # Get the height and width of the image.
    height, width, _ = image.shape
    
    # Create a copy of the input image to write the horizontal position on.
    output_image = image.copy()
    
    # Retreive the x-coordinate of the left shoulder landmark.
    left_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * width)

    # Retreive the x-corrdinate of the right shoulder landmark.
    right_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * width)
    
    # Check if the person is at left that is when both shoulder landmarks x-corrdinates
    # are less than or equal to the x-corrdinate of the center of the image.
    if (right_x <= width//2 and left_x <= width//2):
        
        # Set the person's position to left.
        horizontal_position = 'Left'

    # Check if the person is at right that is when both shoulder landmarks x-corrdinates
    # are greater than or equal to the x-corrdinate of the center of the image.
    elif (right_x >= width//2 and left_x >= width//2):
        
        # Set the person's position to right.
        horizontal_position = 'Right'
    
    # Check if the person is at center that is when right shoulder landmark x-corrdinate is greater than or equal to
    # and left shoulder landmark x-corrdinate is less than or equal to the x-corrdinate of the center of the image.
    elif (right_x >= width//2 and left_x <= width//2):
        
        # Set the person's position to center.
        horizontal_position = 'Center'
        
    # Check if the person's horizontal position and a line at the center of the image is specified to be drawn.
    if draw:

        # Write the horizontal position of the person on the image. 
        cv2.putText(output_image, horizontal_position, (5, height - 10), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
        
        # Draw a line at the center of the image.
        cv2.line(output_image, (width//2, 0), (width//2, height), (255, 255, 255), 2)
        
    # Check if the output image is specified to be displayed.
    if display:

        # Display the output image.
        plt.figure(figsize=[10,10])
        plt.imshow(output_image[:,:,::-1]);plt.title("Output Image");plt.axis('off');
        plt.show()
    
    # Otherwise
    else:
    
        # Return the output image and the person's horizontal position.
        return output_image, horizontal_position

def checkJumpCrouch(image, results, MID_Y=250, draw=False, display=False):
    '''
    This function checks the posture (Jumping, Crouching or Standing) of the person in an image.
    Args:
        image:   The input image with a prominent person whose the posture needs to be checked.
        results: The output of the pose landmarks detection on the input image.
        MID_Y:   The intial center y-coordinate of both shoulders landmarks of the person recorded during starting
                 the game. This will give the idea of the person's height when he is standing straight.
        draw:    A boolean value that is if set to true the function writes the posture on the output image. 
        display: A boolean value that is if set to true the function displays the resultant image and returns nothing.
    Returns:
        output_image: The input image with the person's posture written, if it was specified.
        posture:      The posture (Jumping, Crouching or Standing) of the person in an image.
    '''
    
    # Get the height and width of the image.
    height, width, _ = image.shape
    
    # Create a copy of the input image to write the posture label on.
    output_image = image.copy()
    
    # Retreive the y-coordinate of the left shoulder landmark.
    left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * height)

    # Retreive the y-coordinate of the right shoulder landmark.
    right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * height)

    # Calculate the y-coordinate of the mid-point of both shoulders.
    actual_mid_y = abs(right_y + left_y) // 2
    
    # Calculate the upper and lower bounds of the threshold.
    lower_bound = MID_Y-15
    upper_bound = MID_Y+100
    
    # Check if the person has jumped that is when the y-coordinate of the mid-point 
    # of both shoulders is less than the lower bound.
    if (actual_mid_y < lower_bound):
        
        # Set the posture to jumping.
        posture = 'Jumping'
    
    # Check if the person has crouched that is when the y-coordinate of the mid-point 
    # of both shoulders is greater than the upper bound.
    elif (actual_mid_y > upper_bound):
        
        # Set the posture to crouching.
        posture = 'Crouching'
    
    # Otherwise the person is standing and the y-coordinate of the mid-point 
    # of both shoulders is between the upper and lower bounds.    
    else:
        
        # Set the posture to Standing straight.
        posture = 'Standing'
        
    # Check if the posture and a horizontal line at the threshold is specified to be drawn.
    if draw:

        # Write the posture of the person on the image. 
        cv2.putText(output_image, posture, (5, height - 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
        
        # Draw a line at the intial center y-coordinate of the person (threshold).
        cv2.line(output_image, (0, MID_Y),(width, MID_Y),(255, 255, 255), 2)
        
    # Check if the output image is specified to be displayed.
    if display:

        # Display the output image.
        plt.figure(figsize=[10,10])
        plt.imshow(output_image[:,:,::-1]);plt.title("Output Image");plt.axis('off');
        plt.show()
    
    # Otherwise
    else:
    
        # Return the output image and posture indicating whether the person is standing straight or has jumped, or crouched.
        return output_image, posture

def test_image():
    """Test the pose detection on a sample image from the media folder"""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to sample image
        img_path = os.path.join(current_dir, 'media', 'sample.jpg')
        
        if not os.path.exists(img_path):
            print(f"Error: Sample image not found at {img_path}")
            available_images = [f for f in os.listdir(os.path.join(current_dir, 'media')) 
                               if f.endswith('.jpg') or f.endswith('.png')]
            if available_images:
                print(f"Available images: {', '.join(available_images)}")
                img_path = os.path.join(current_dir, 'media', available_images[0])
                print(f"Using alternative image: {available_images[0]}")
            else:
                print("No images found in the media directory.")
                return
        
        # Read the sample image
        print(f"Reading image from: {img_path}")
        image = cv2.imread(img_path)
        
        if image is None:
            print(f"Error: Could not load image from {img_path}")
            return
            
        # Perform pose detection
        detectPose(image, pose_image, draw=True, display=True)
        
    except Exception as e:
        print(f"Error testing image: {e}")

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

def test_hands_joined():
    """Test the hands joined detection using webcam"""
    try:
        # Try to find an available camera
        camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara. Verifique que:")
            print("  1. Su cámara esté conectada y funcionando")
            print("  2. No esté siendo utilizada por otra aplicación")
            print("  3. Tenga los permisos necesarios para acceder a la cámara")
            print("  4. Los controladores de la cámara estén instalados correctamente")
            return
            
        # Initialize the VideoCapture object to read from the webcam with camera index 3
        camera_video = cv2.VideoCapture(3)
        if not camera_video.isOpened():
            print(f"Error: No se pudo abrir la cámara con índice {camera_index}")
            return
            
        camera_video.set(3, 640)  # Cambiado de 1280 a 640
        camera_video.set(4, 480)  # Cambiado de 960 a 480
        
        # Create named window for resizing purposes
        cv2.namedWindow('Hands Joined Test', cv2.WINDOW_NORMAL)
        
        print("Press ESC to exit the test")
        
        # Iterate until the webcam is accessed successfully
        while camera_video.isOpened():
            # Read a frame
            ok, frame = camera_video.read()
            
            # Check if frame is not read properly
            if not ok:
                print("Error: No se pudo leer un fotograma de la cámara")
                break
            
            # Flip the frame horizontally for natural (selfie-view) visualization
            frame = cv2.flip(frame, 1)
            
            # Perform the pose detection
            frame, results = detectPose(frame, pose_video, draw=True)
            
            # Check if the pose landmarks are detected
            if results.pose_landmarks:
                # Check if the hands are joined
                frame, _ = checkHandsJoined(frame, results, draw=True)
            
            # Display the frame
            cv2.imshow('Hands Joined Test', frame)
            
            # Wait for 1ms. If ESC is pressed, exit
            k = cv2.waitKey(1) & 0xFF
            if k == 27:  # ESC key
                break
        
        # Release the webcam and close the window
        camera_video.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error testing hands joined: {e}")
        import traceback
        traceback.print_exc()

def test_horizontal_movement():
    """Test the horizontal movement detection using webcam"""
    try:
        # Try to find an available camera
        camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            return
            
        # Initialize the VideoCapture object to read from the webcam
        camera_video = cv2.VideoCapture(camera_index)
        if not camera_video.isOpened():
            print(f"Error: No se pudo abrir la cámara con índice {camera_index}")
            return
            
        camera_video.set(3, 640)  # Cambiado de 1280 a 640
        camera_video.set(4, 480)  # Cambiado de 960 a 480
        
        # Create named window for resizing purposes
        cv2.namedWindow('Horizontal Movement Test', cv2.WINDOW_NORMAL)
        
        print("Press ESC to exit the test")
        
        # Iterate until the webcam is accessed successfully
        while camera_video.isOpened():
            # Read a frame
            ok, frame = camera_video.read()
            
            # Check if frame is not read properly
            if not ok:
                print("Error: No se pudo leer un fotograma de la cámara")
                break
            
            # Flip the frame horizontally for natural (selfie-view) visualization
            frame = cv2.flip(frame, 1)
            
            # Perform the pose detection
            frame, results = detectPose(frame, pose_video, draw=True)
            
            # Check if the pose landmarks are detected
            if results.pose_landmarks:
                # Check horizontal position
                frame, _ = checkLeftRight(frame, results, draw=True)
            
            # Display the frame
            cv2.imshow('Horizontal Movement Test', frame)
            
            # Wait for 1ms. If ESC is pressed, exit
            k = cv2.waitKey(1) & 0xFF
            if k == 27:  # ESC key
                break
        
        # Release the webcam and close the window
        camera_video.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error testing horizontal movement: {e}")
        import traceback
        traceback.print_exc()

def test_vertical_movement():
    """Test the vertical movement (jump/crouch) detection using webcam"""
    try:
        # Try to find an available camera
        camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            return
            
        # Initialize the VideoCapture object to read from the webcam
        camera_video = cv2.VideoCapture(camera_index)
        if not camera_video.isOpened():
            print(f"Error: No se pudo abrir la cámara con índice {camera_index}")
            return
            
        camera_video.set(3, 640)  # Cambiado de 1280 a 640
        camera_video.set(4, 480)  # Cambiado de 960 a 480
        
        # Create named window for resizing purposes
        cv2.namedWindow('Vertical Movement Test', cv2.WINDOW_NORMAL)
        
        print("Press ESC to exit the test")
        
        # Iterate until the webcam is accessed successfully
        while camera_video.isOpened():
            # Read a frame
            ok, frame = camera_video.read()
            
            # Check if frame is not read properly
            if not ok:
                print("Error: No se pudo leer un fotograma de la cámara")
                break
            
            # Flip the frame horizontally for natural (selfie-view) visualization
            frame = cv2.flip(frame, 1)
            
            # Perform the pose detection
            frame, results = detectPose(frame, pose_video, draw=True)
            
            # Check if the pose landmarks are detected
            if results.pose_landmarks:
                # Check vertical position (jump/crouch)
                # Use a default mid Y value for testing (can be adjusted)
                frame, _ = checkJumpCrouch(frame, results, draw=True)
            
            # Display the frame
            cv2.imshow('Vertical Movement Test', frame)
            
            # Wait for 1ms. If ESC is pressed, exit
            k = cv2.waitKey(1) & 0xFF
            if k == 27:  # ESC key
                break
        
        # Release the webcam and close the window
        camera_video.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error testing vertical movement: {e}")
        import traceback
        traceback.print_exc()

def play_game():
    """Main function to play Subway Surfers with pose detection"""
    try:
        # Abrir automáticamente la URL de Subway Surfers
        print("Abriendo Subway Surfers en el navegador...")
        webbrowser.open("https://subwaysurfersgame.io/online")
        
        # Try to find an available camera
        camera_index = try_available_cameras()
        if camera_index == -1:
            print("Error: No se pudo acceder a ninguna cámara.")
            print("  1. Verifique que su cámara esté conectada y funcionando")
            print("  2. No esté siendo utilizada por otra aplicación")
            print("  3. Tenga los permisos necesarios para acceder a la cámara")
            print("  4. Los controladores de la cámara estén instalados correctamente")
            return
            
        # Initialize the VideoCapture object to read from the webcam
        camera_video = cv2.VideoCapture(camera_index)
        if not camera_video.isOpened():
            print(f"Error: No se pudo abrir la cámara con índice {camera_index}")
            return
            
        camera_video.set(3, 640)  # Cambiado de 1280 a 640
        camera_video.set(4, 480)  # Cambiado de 960 a 480
        
        # Create named window for resizing purposes
        cv2.namedWindow('Subway Surfers with Pose Detection', cv2.WINDOW_NORMAL)
        
        # Initialize variables
        time1 = 0
        game_started = False
        x_pos_index = 1
        y_pos_index = 1
        MID_Y = None
        counter = 0
        num_of_frames = 10
        
        # Imprimir instrucciones detalladas en español
        print("\n============== INSTRUCCIONES ==============")
        print("1. Colócate frente a la cámara donde pueda verse todo tu cuerpo")
        print("2. Para INICIAR el juego: Junta tus manos frente a ti (como si rezaras o aplaudieras).")
        print("3. Para controlar al personaje:")
        print("   - Muévete a la IZQUIERDA o DERECHA para cambiar de carril")
        print("   - SALTA para saltar obstáculos")
        print("   - AGÁCHATE para deslizarte bajo obstáculos")
        print("4. Para PAUSAR/REANUDAR: Junta tus manos nuevamente")
        print("5. Presiona ESC para salir")
        print("=========================================\n")
        
        # Contador de frames para mostrar la instrucción animada
        instruction_frame = 0
        max_instruction_frames = 90  # ~3 segundos a 30fps
        
        # Iterate until the webcam is accessed successfully
        while camera_video.isOpened():
            # Read a frame
            ok, frame = camera_video.read()
            
            # Check if frame is not read properly
            if not ok:
                print("Error: No se pudo leer un fotograma de la cámara")
                break
            
            # Flip the frame horizontally for natural (selfie-view) visualization
            frame = cv2.flip(frame, 1)
            
            # Get the height and width of the frame
            frame_height, frame_width, _ = frame.shape
            
            # Perform the pose detection
            frame, results = detectPose(frame, pose_video, draw=game_started)
            
            # Check if the pose landmarks are detected
            if results.pose_landmarks:
                
                # Check if the game has started
                if game_started:
                    
                    # Commands to control the horizontal movements of the character
                    frame, horizontal_position = checkLeftRight(frame, results, draw=True)
                    
                    # Check if the person has moved to left from center or to center from right
                    if (horizontal_position=='Left' and x_pos_index!=0) or (horizontal_position=='Center' and x_pos_index==2):
                        
                        # Press the left arrow key
                        pyautogui.press('left')
                        
                        # Update the horizontal position index of the character
                        x_pos_index -= 1               

                    # Check if the person has moved to Right from center or to center from left
                    elif (horizontal_position=='Right' and x_pos_index!=2) or (horizontal_position=='Center' and x_pos_index==0):
                        
                        # Press the right arrow key
                        pyautogui.press('right')
                        
                        # Update the horizontal position index of the character
                        x_pos_index += 1
                
                # Otherwise if the game has not started
                else:
                    # Mostrar instrucciones animadas en la pantalla
                    instruction_frame = (instruction_frame + 1) % max_instruction_frames
                    
                    # Instrucción principal
                    cv2.putText(frame, 'JUNTA TUS MANOS FRENTE A TI', (frame_width//2 - 250, frame_height - 100), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    
                    # Instrucciones adicionales que parpadean
                    if instruction_frame < max_instruction_frames // 2:
                        cv2.putText(frame, 'Como si rezaras o aplaudieras', (frame_width//2 - 200, frame_height - 60), 
                                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
                        
                        # Dibujar iconos de manos
                        hand_center_x = frame_width // 2
                        hand_center_y = frame_height // 2
                        
                        # Dibujar manos juntas como un simple diagrama
                        cv2.circle(frame, (hand_center_x - 30, hand_center_y), 40, (0, 255, 0), 2)
                        cv2.circle(frame, (hand_center_x + 30, hand_center_y), 40, (0, 255, 0), 2)
                        
                        # Línea para juntar las manos
                        cv2.line(frame, (hand_center_x - 10, hand_center_y), 
                                (hand_center_x + 10, hand_center_y), (0, 255, 0), 5)
                
                # Command to Start or resume the game
                if checkHandsJoined(frame, results)[1] == 'Hands Joined':
                    
                    # Mostrar visualmente que las manos están unidas correctamente
                    cv2.putText(frame, '¡MANOS UNIDAS!', (10, 130), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    
                    # Increment the count of consecutive frames with +ve condition
                    counter += 1
                    
                    # Mostrar contador para que el usuario sepa cuánto falta para la acción
                    cv2.putText(frame, f'Mantenlas unidas: {counter}/{num_of_frames}', 
                                (10, 170), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                    
                    # Check if the counter is equal to the required number of consecutive frames
                    if counter == num_of_frames:
                        
                        # Check if the game has not started yet
                        if not(game_started):
                            
                            # Update the value of the variable that stores the game state
                            game_started = True
                            
                            # Retreive the y-coordinate of the left shoulder landmark
                            left_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * frame_height)
                            
                            # Retreive the y-coordinate of the right shoulder landmark
                            right_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * frame_height)
                            
                            # Calculate the intial y-coordinate of the mid-point of both shoulders
                            MID_Y = abs(right_y + left_y) // 2
                            
                            # Move to 1300, 800, then click the left mouse button to start the game
                            pyautogui.click(x=1300, y=800, button='left')
                            
                            # Mensaje de confirmación
                            print("\n¡Juego iniciado! Ahora puedes controlar al personaje con tus movimientos.")
                        
                        # Otherwise if the game has started
                        else:
                            
                            # Press the space key
                            pyautogui.press('space')
                            
                            # Mensaje visual
                            cv2.putText(frame, '¡PAUSA/CONTINUAR!', (frame_width//2 - 150, 100), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                        
                        # Update the counter value to zero
                        counter = 0
                        
                # Otherwise if the left and right hands are not joined
                else:
                    
                    # Update the counter value to zero
                    counter = 0
                    
                # Commands to control the vertical movements of the character
                if MID_Y:
                    
                    # Get posture (jumping, crouching or standing) of the person
                    frame, posture = checkJumpCrouch(frame, results, MID_Y, draw=True)
                    
                    # Check if the person has jumped
                    if posture == 'Jumping' and y_pos_index == 1:
                        
                        # Press the up arrow key
                        pyautogui.press('up')
                        
                        # Update the vertical position index of the character
                        y_pos_index += 1 
                        
                    # Check if the person has crouched
                    elif posture == 'Crouching' and y_pos_index == 1:
                        
                        # Press the down arrow key
                        pyautogui.press('down')
                        
                        # Update the vertical position index of the character
                        y_pos_index -= 1
                    
                    # Check if the person has stood
                    elif posture == 'Standing' and y_pos_index != 1:
                        
                        # Update the vertical position index of the character
                        y_pos_index = 1
            
            # Otherwise if the pose landmarks in the frame are not detected
            else:
                
                # Update the counter value to zero
                counter = 0
                
                # Mostrar mensaje de que no se detecta a la persona
                cv2.putText(frame, 'No se detecta persona - Ponte frente a la camara', (10, frame_height - 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
            # Calculate the frames updates in one second
            
            # Set the time for this frame to the current time
            time2 = time()
            
            # Check if the difference between the previous and this frame time > 0 to avoid division by zero
            if (time2 - time1) > 0:
            
                # Calculate the number of frames per second
                frames_per_second = 1.0 / (time2 - time1)
                
                # Write the calculated number of frames per second on the frame
                cv2.putText(frame, 'FPS: {}'.format(int(frames_per_second)), (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)
            
            # Update the previous frame time to this frame time
            time1 = time2
            
            # Display the frame
            cv2.imshow('Subway Surfers with Pose Detection', frame)
            
            # Wait for 1ms. If ESC is pressed, exit
            k = cv2.waitKey(1) & 0xFF
            
            if(k == 27):
                break
                
        # Release the VideoCapture object and close the windows
        camera_video.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error playing game: {e}")
        import traceback
        traceback.print_exc()

def show_help():
    """Show usage information for the script"""
    print("""
Subway Surfers Pose Detection Controller
----------------------------------------
This script lets you control the Subway Surfers game using body movements detected by your webcam.

Commands:
  --test-image         Test pose detection on a sample image
  --test-hands         Test hand join detection using webcam
  --test-horizontal    Test horizontal movement detection using webcam
  --test-vertical      Test vertical movement detection using webcam
  --play               Start the game controller
  --help               Show this help message

Instructions:
1. Start the Subway Surfers game in your browser (https://www.kiloo.com/subway-surfers/)
2. Position yourself in front of the webcam
3. Join both hands to start or resume the game
4. Move left/right to control horizontal movement
5. Jump/crouch to control vertical movement
6. Press ESC to exit

Requirements:
- Python 3.8+
- OpenCV, MediaPipe, PyAutoGUI, Matplotlib

Example:
  python subway_surfers_pose_detection.py --play
""")


def main():
    """Main function to parse arguments and run the appropriate function"""
    parser = argparse.ArgumentParser(description='Subway Surfers Pose Detection Controller')
    parser.add_argument('--test-image', action='store_true', help='Test pose detection on a sample image')
    parser.add_argument('--test-hands', action='store_true', help='Test hand join detection using webcam')
    parser.add_argument('--test-horizontal', action='store_true', help='Test horizontal movement detection using webcam')
    parser.add_argument('--test-vertical', action='store_true', help='Test vertical movement detection using webcam')
    parser.add_argument('--play', action='store_true', help='Start the game controller')
    # Removed the custom --help argument as it conflicts with built-in help
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        show_help()
        return
    
    # Run the appropriate function
    if args.test_image:
        test_image()
    elif args.test_hands:
        test_hands_joined()
    elif args.test_horizontal:
        test_horizontal_movement()
    elif args.test_vertical:
        test_vertical_movement()
    elif args.play:
        play_game()


if __name__ == "__main__":
    main()