"""
Script para detectar y probar cámaras disponibles en Windows
Este script intentará detectar todas las cámaras disponibles en tu sistema y mostrar su imagen.
"""

import cv2
import time
import platform
import os

def list_available_cameras():
    """
    Intenta encontrar todas las cámaras disponibles en el sistema
    y muestra sus características
    """
    print("=" * 50)
    print("DETECTOR DE CÁMARAS")
    print("=" * 50)
    print(f"Sistema: {platform.system()} {platform.release()}")
    print(f"Versión de OpenCV: {cv2.__version__}")
    print("=" * 50)
    print("Buscando cámaras disponibles...")
    print("=" * 50)
    
    # Número máximo de índices de cámara a probar
    max_cameras = 10
    available_cameras = []
    
    for index in range(max_cameras):
        cap = cv2.VideoCapture(index, cv2.CAP_ANY)  # Probar con diferentes APIs
        if cap.isOpened():
            # Obtener información sobre la cámara
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"Cámara {index}: DISPONIBLE")
            print(f"  - Resolución: {width}x{height}")
            print(f"  - FPS: {fps}")
            
            # Leer un frame para verificar que funciona
            ret, frame = cap.read()
            if ret:
                print(f"  - Lectura de imagen: EXITOSA")
                available_cameras.append(index)
            else:
                print(f"  - Lectura de imagen: ERROR (La cámara existe pero no puede capturar imágenes)")
            
            # Liberar la cámara
            cap.release()
        else:
            print(f"Cámara {index}: NO DISPONIBLE")
    
    print("=" * 50)
    if available_cameras:
        print(f"Se encontraron {len(available_cameras)} cámaras disponibles: {available_cameras}")
    else:
        print("No se encontró ninguna cámara disponible")
    
    return available_cameras

def test_camera_view(camera_index):
    """
    Muestra la vista de la cámara seleccionada
    """
    print(f"Probando cámara {camera_index}...")
    
    # Intentar con múltiples backends de cámara en caso de fallo
    backends = [
        (cv2.CAP_ANY, "Automático"),
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Media Foundation"),
    ]
    
    for backend, name in backends:
        print(f"Intentando con backend: {name}")
        cap = cv2.VideoCapture(camera_index, backend)
        
        if not cap.isOpened():
            print(f"No se pudo abrir la cámara {camera_index} con backend {name}")
            continue
            
        # Configurar resolución (puedes ajustarla)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        window_name = f"Cámara {camera_index} - Backend: {name}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        try:
            start_time = time.time()
            frame_count = 0
            
            print("Presiona ESC para salir, o ESPACIO para guardar una imagen")
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("Error al leer frame")
                    break
                    
                # Mostrar FPS
                frame_count += 1
                elapsed_time = time.time() - start_time
                if elapsed_time > 1:
                    fps = frame_count / elapsed_time
                    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    frame_count = 0
                    start_time = time.time()
                
                # Mostrar índice de cámara y backend
                cv2.putText(frame, f"Cámara: {camera_index}, Backend: {name}", 
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(window_name, frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC para salir
                    break
                elif key == 32:  # ESPACIO para guardar imagen
                    filename = f"camera_{camera_index}_capture.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"Imagen guardada como: {filename}")
                
            cap.release()
            cv2.destroyWindow(window_name)
            return True
            
        except Exception as e:
            print(f"Error al probar la cámara: {e}")
            if cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
    
    return False

def show_camera_troubleshooting():
    """
    Muestra consejos para solucionar problemas con la cámara
    """
    print("\n" + "=" * 50)
    print("SOLUCIÓN DE PROBLEMAS CON LA CÁMARA")
    print("=" * 50)
    print("Si no se detectan cámaras o tienes problemas:")
    print("1. Verifica que la cámara esté conectada físicamente")
    print("2. Abre la aplicación 'Cámara' de Windows para ver si funciona allí")
    print("3. Verifica los permisos de la cámara en:")
    print("   Configuración > Privacidad y seguridad > Cámara")
    print("4. Comprueba si otros programas están usando la cámara")
    print("5. Actualiza o reinstala los controladores de la cámara")
    print("6. En algunas laptops, hay una tecla Fn+F_ para habilitar/deshabilitar la cámara")
    print("7. Comprueba el Administrador de dispositivos de Windows para ver si hay problemas")
    print("=" * 50)

def main():
    """
    Función principal del script
    """
    cameras = list_available_cameras()
    
    if not cameras:
        print("No se encontraron cámaras disponibles.")
        show_camera_troubleshooting()
        return
    
    print("\nSelecciona una cámara para probar:")
    for idx in cameras:
        print(f"{idx}: Cámara {idx}")
    
    try:
        selection = input("\nIngresa el número de la cámara a probar (o presiona Enter para probarlas todas): ")
        
        if selection.strip() == "":
            # Probar todas las cámaras
            for idx in cameras:
                test_camera_view(idx)
        else:
            selected_idx = int(selection)
            if selected_idx in cameras:
                test_camera_view(selected_idx)
            else:
                print(f"La cámara {selected_idx} no está disponible")
                
    except ValueError:
        print("Por favor, ingresa un número válido")
    except KeyboardInterrupt:
        print("\nDetección de cámaras interrumpida por el usuario")
    finally:
        print("\nPrograma finalizado")
        show_camera_troubleshooting()

if __name__ == "__main__":
    main()