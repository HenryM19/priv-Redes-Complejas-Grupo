# Claude + Blender: Generación Automática de Modelos 3D para Robótica

## ¿Qué es MCP y cómo conecta Claude con Blender?

El **Model Context Protocol (MCP)** es un protocolo abierto que permite a Claude conectarse directamente con aplicaciones externas como Blender, VS Code, GitHub o Fusion 360. En lugar de solo generar texto, Claude puede ejecutar acciones reales dentro de esas herramientas.

Para el caso de Blender, el servidor MCP expone una herramienta llamada `execute_blender_code()` que recibe un script Python (`bpy`) y lo ejecuta en tiempo real dentro de la aplicación abierta.

---

## Flujo completo: del texto al modelo 3D

```
Usuario
  │
  │  "Crea un brazo 6-DOF con gripper paralelo"
  ▼
Claude (LLM)
  │  Interpreta la instrucción, razona sobre geometría
  │  y genera el código necesario
  ▼
MCP Server — Blender
  │  execute_blender_code( script )
  ▼
Script Python / bpy
  │  bpy.ops.mesh.primitive_cylinder_add(…)
  │  bpy.ops.object.modifier_add(type='ARMATURE')
  │  …
  ▼
Blender — Ejecución
  │  Crea eslabones, joints, asigna masas y fricción
  ▼
Modelo 3D + URDF exportado
   robot_arm.urdf  →  Isaac Lab / ROS 2
```

En ningún paso el usuario escribe código manualmente. La instrucción en lenguaje natural es suficiente.

---

## Ejemplo real: prompt de entrada

```
"Crea un brazo robótico industrial con 6 articulaciones,
gripper paralelo de 2 dedos,
base fija en z = 0"
```

### Lo que Claude interpreta y genera automáticamente

| Aspecto | Resultado |
|---|---|
| **Estructura cinemática** | 6 eslabones (links) + 6 articulaciones (joints) + gripper 2 DOF |
| **Proporciones realistas** | Dimensiones basadas en robots industriales tipo FANUC / UR |
| **Parámetros dinámicos** | Masas, inercias, fricción y límites de movimiento por joint |
| **Formato exportable** | URDF compatible con ROS 2 e Isaac Lab, listo para simular |

> **Resultado:** sin escribir una sola línea de código, se obtiene un modelo completamente parametrizado, validado y listo para simulación.

---

## Herramientas del ecosistema

Claude puede conectarse simultáneamente con múltiples herramientas a través de sus servidores MCP:

- **Blender** — modelos 3D y archivos URDF
- **Fusion 360** — CAD mecánico y análisis FEA
- **VS Code** — edición y debugging de scripts
- **GitHub** — control de versiones del proyecto
- **Google Drive** — documentación y especificaciones


Estas herramientas permiten: 
- Generar documentación
- Generar software 
- Adquisición de datos de sensores 

Todo esto con apoyo de agentes de IA
---

## Por qué esto cambia el prototipado en robótica

Sin IA, crear un modelo URDF de un brazo robótico requiere conocer la API de Blender (`bpy`), entender la estructura XML del formato URDF, calcular manualmente inercias y límites de joints, y corregir errores iterativamente. El proceso toma días.

Con Claude + MCP, la descripción en lenguaje natural se traduce directamente a un modelo funcional. El tiempo de prototipado pasa de semanas a horas. 
