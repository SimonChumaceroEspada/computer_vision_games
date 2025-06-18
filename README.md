# Computer Vision Games

Sistema de juegos controlados mediante visión por computadora que permite jugar videojuegos populares utilizando movimientos corporales y gestos de las manos.

## Descripción

Este proyecto utiliza técnicas de visión por computadora y aprendizaje automático para detectar movimientos corporales y gestos de las manos, permitiendo controlar diferentes videojuegos sin necesidad de teclado o mouse. El sistema incluye controladores para:

- **Arcade 1942**: Control del clásico juego de disparos mediante gestos de las manos
- **Geometry Dash**: Juego de plataformas rítmico controlado por gestos de las manos
- **Subway Surfers**: Juego endless runner controlado mediante detección de pose corporal completa

El proyecto está diseñado para ser accesible, educativo y divertido, demostrando aplicaciones prácticas de la visión por computadora.

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
- **Saltar**: Gesto de pellizco

**Configuración recomendada:**
- Colócate a una distancia de 50-70 cm de la cámara
- El fondo debe contrastar con tus manos para una mejor detección

### Subway Surfers

Control del juego endless runner mediante detección de pose corporal completa utilizando MediaPipe.

**Controles:**

1. **Iniciar/Pausar el juego**:
   - Junta tus manos frente a ti una delante de la otra
   - Mantén las manos unidas por unos segundos hasta que aparezca la confirmación
   - Este mismo gesto se usa tanto para iniciar como para pausar/reanudar el juego

2. **Movimiento horizontal (cambio de carril)**:
   - **Moverse a la izquierda**: Inclina tu cuerpo hacia la izquierda
   - **Moverse a la derecha**: Inclina tu cuerpo hacia la derecha
   - **Regresar al centro**: Regresa a una posición corporal centrada

3. **Movimientos verticales**:
   - **Saltar**: Salta físicamente (levanta tus hombros del nivel inicial)
   - **Deslizarse/Agacharse**: Agáchate o baja tus hombros debajo del nivel inicial
   - **Posición normal**: Mantente de pie en posición erguida

**Configuración recomendada:**
- **Distancia**: Colócate a 1.5-2 metros de la cámara
- **Espacio**: Asegúrate de tener suficiente espacio para moverte en todas las direcciones
- **Encuadre**: La cámara debe capturar tu cuerpo completo desde la cabeza hasta las rodillas
- **Iluminación**: Buena iluminación frontal para una detección precisa
- **Fondo**: Un fondo contrastante ayuda a mejorar la detección de pose

**Consejos para un mejor control**:
- Realiza movimientos deliberados y mantén las posiciones por un momento
- Evita movimientos muy rápidos o bruscos que puedan confundir al detector
- Mantén una postura erguida cuando no estés realizando acciones específicas
- El sistema detecta los movimientos basándose en la posición de tus hombros como referencia

## Solución de problemas

- **No se detecta la cámara**: Verifica que la cámara esté conectada y no esté siendo utilizada por otra aplicación
- **Baja tasa de cuadros (FPS)**: Cierra aplicaciones en segundo plano y asegúrate de tener buena iluminación
- **Detección imprecisa**: Mejora la iluminación y asegúrate de tener un fondo uniforme que contraste con tu cuerpo o manos



