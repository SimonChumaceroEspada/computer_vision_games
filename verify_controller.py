#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de verificación rápida para el gesto de barril roll
"""

import sys
import os

# Agregar el directorio actual al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar la clase HandController
from arcade_1942_mouse_controller import HandController

def test_controller_initialization():
    """Prueba la inicialización del controlador"""
    try:
        print("🔧 Inicializando HandController...")
        controller = HandController()
        
        # Verificar que todas las variables requeridas estén inicializadas
        required_attrs = [
            'last_barrel_roll_time',
            'last_shoot_time', 
            'last_start_time',
            'last_select_time',
            'gesture_cooldowns'
        ]
        
        for attr in required_attrs:
            if hasattr(controller, attr):
                print(f"✅ {attr}: {getattr(controller, attr)}")
            else:
                print(f"❌ {attr}: NO ENCONTRADO")
                return False
        
        print("✅ Todas las variables están correctamente inicializadas")
        
        # Verificar cooldowns
        print("\n🕰️ Verificando cooldowns:")
        for key, value in controller.gesture_cooldowns.items():
            print(f"   {key}: {value} segundos")
        
        print("\n🎮 Controlador listo para usar!")
        print("Ejecuta: python arcade_1942_mouse_controller.py --test")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al inicializar: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== VERIFICACIÓN DEL CONTROLADOR ===")
    success = test_controller_initialization()
    if success:
        print("\n🎉 ¡Todo funciona correctamente!")
    else:
        print("\n💥 Hay problemas que necesitan ser corregidos")
