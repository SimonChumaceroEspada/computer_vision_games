# Computer Vision Games

Sistema de juegos controlados mediante visión por computadora que permite jugar videojuegos populares utilizando movimientos corporales y gestos de las manos.

## Descripción

Este proyecto utiliza técnicas de visión por computadora y aprendizaje automático para detectar movimientos corporales y gestos de las manos, permitiendo controlar diferentes videojuegos sin necesidad de teclado o mouse. El sistema incluye controladores para:

- **Arcade 1942**: Control del clásico juego de disparos mediante gestos de las manos
- **Geometry Dash**: Juego de plataformas rítmico controlado por gestos de las manos
- **Subway Surfers**: Juego endless runner controlado mediante detección de pose corporal completa

El proyecto está diseñado para ser accesible, educativo y divertido, demostrando aplicaciones prácticas de la visión por computadora.

## Datos de entrada y herramientas

### Datos de entrada
El sistema procesa fundamentalmente los siguientes tipos de datos de entrada:

1. **Secuencias de video en tiempo real**: Capturadas a través de la cámara web del usuario.
   - Resolución típica: 480x320 píxeles (configurable)
   - Tasa de cuadros: Variable según hardware, típicamente 15-30 FPS
   - Formato: BGR (OpenCV) convertido a RGB para procesamiento

2. **Landmarks de manos**: Puntos clave en las manos detectadas:
   - 21 puntos de referencia para cada mano (nudillos, articulaciones y puntas de los dedos)
   - Coordenadas normalizadas (x,y,z) para cada punto
   - Información de confianza de la detección

3. **Poses corporales completas** (para Subway Surfers):
   - 33 puntos de referencia de pose del cuerpo
   - Coordenadas espaciales para cada punto
   - Valores de confianza para cada punto detectado

### Flujo de procesamiento de datos
1. **Captura**: Obtención de frames de video mediante OpenCV
2. **Preprocesamiento**: Redimensionamiento y conversión de espacios de color
3. **Detección**: Aplicación de modelos de MediaPipe para detectar manos o poses
4. **Extracción de características**: Cálculo de posiciones relativas y reconocimiento de gestos
5. **Mapeo**: Traducción de gestos y movimientos a comandos de juego mediante PyAutoGUI

### Ejemplos visuales de datos de entrada

La entrada principal del sistema son imágenes como estas, donde se detectan los landmarks de las manos:

```
|-------------------------|
|                         |
|       👋               |
|      /                  |
|     /                   |
|    /                    |
|   /                     |
|  /                      |
| /                       |
|/                        |
|-------------------------|
  Frame de video con mano
```

Estos landmarks se procesan en tiempo real y se convierten en comandos de control para los juegos, según los gestos detectados.

## Instalación

### Requisitos previos
- Python 3.10 o superior
- Webcam o cámara USB
- Windows 10/11 (para otras plataformas pueden requerirse ajustes adicionales)

### Pasos de instalación

1. Clona o descarga este repositorio en tu computadora
2. Ejecuta el script de instalación automática:

   ```
   setup.bat
   ```

   O instala las dependencias manualmente:

   ```
   pip install -r requirements.txt
   ```

3. Verifica que tu cámara esté conectada y funcionando correctamente

## Uso

1. Ejecuta el menú principal de la aplicación:

   ```
   python game_menu.py
   ```

2. En la interfaz gráfica:
   - Selecciona la cámara que deseas utilizar
   - Puedes probar la cámara con el botón "Test Selected Camera"
   - Selecciona el juego que deseas jugar y haz clic en el botón correspondiente

3. Sigue las instrucciones en pantalla para cada juego

## Instrucciones por juego

### Arcade 1942

Control del clásico juego shoot-em-up mediante gestos de las manos.

**Controles:**
- **Mover el avión**: Mueve tu mano abierta por la pantalla
- **Disparar**: Cierra el puño
- **Hacer barrel roll**: Movimiento rápido hacia la izquierda o derecha

**Configuración recomendada:**
- Colócate a una distancia de 50-60 cm de la cámara
- Asegúrate de tener buena iluminación para la detección de gestos

### Geometry Dash

Control del juego de plataformas rítmico mediante gestos de las manos.

**Controles:**
- **Saltar**: Levanta la mano rápidamente
- **Volar**: Mantén la mano en posición elevada

**Configuración recomendada:**
- Colócate a una distancia de 50-70 cm de la cámara
- El fondo debe contrastar con tus manos para una mejor detección

### Subway Surfers

Control del juego endless runner mediante detección de pose corporal completa.

**Controles:**
- **Iniciar/Pausar**: Junta las manos frente a ti (como si aplaudieras)
- **Moverse a la izquierda/derecha**: Inclina tu cuerpo a la izquierda o derecha
- **Saltar**: Salta físicamente
- **Deslizarse**: Agáchate

**Configuración recomendada:**
- Colócate a una distancia de 1.5-2 metros de la cámara
- Se necesita espacio suficiente para moverte
- La cámara debe capturar tu cuerpo completo

## Solución de problemas

- **No se detecta la cámara**: Verifica que la cámara esté conectada y no esté siendo utilizada por otra aplicación
- **Baja tasa de cuadros (FPS)**: Cierra aplicaciones en segundo plano y asegúrate de tener buena iluminación
- **Detección imprecisa**: Mejora la iluminación y asegúrate de tener un fondo uniforme que contraste con tu cuerpo o manos



