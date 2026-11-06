# MANAAplot

*Medidor Automático de Nivel de Agua en Arroyos*

DESCARGAS
| Sistema operativo | Descarga |
| - | - |
| Linux (x86-64) | [Versión linux-v0.3-beta](https://github.com/GallardoFanchinThiago/MANAAplot/releases/download/v0.3-beta/manaaplot-v0.3-linux-beta) |
| Windows (x86-64) | [Versión windows-v0.3-beta](https://github.com/GallardoFanchinThiago/MANAAplot/releases/download/v0.3-beta/manaaplot-v0.3-windows-beta.exe) |

INSTRUCCIÓN DE USO
1. **Instalación:** En la sección DESCARGAS elegir la versión correspondiente a tu sistema operativo, instalarlo y ejecutar el archivo
<p align=center> <img width="414" height="333" alt="image" src="https://github.com/user-attachments/assets/96e60fe9-cd30-411c-9674-d3795926d9fe" /> </p>

2. **Abrir archivo:** Para abrir un archivo de datos presionar el botón "Elegir archivo", esto abre un buscador de archivos, elige manualmente un archivo.
<img width="227" height="185" alt="image" src="https://github.com/user-attachments/assets/25ca2a56-b92a-4c75-8e5d-c039292bfa21" />

3. **Procesar los datos:** Presione el botón "Crudo" y elija la opción "Procesado"


1. Formato de archivos
   Formato txt: El archivo a introducir debe ser un .txt o .csv con las siguientes columnas en orden obligatorio independientemente del nombre: Fecha-hora (1), distancia (2),
   temperatura (3), presión atmosférica (4), altitud barométrica (5), y humedad relativa (6); con la siguiente estructura y nombres:
   **FECHA_HORA_DT, DISTANCIA_CM, TEMPERATURA_C, PRESION_ATM, HUMEDAD_PCT**

   Ráfagas del medidor: El medidor registra datos de forma periódica, tomando ~10 datos, 1 cada 300 ms, y entra en reposo durante ~10 minutos, esto tiene como objetivo corregir
   ruido de las observaciones, tomando el valor más representativo del periodo de ~10 minutos. De cada ráfaga se calcula la moda, y en caso de ser una una ráfaga multimodal, se
   toma la mediana de estos valores.

   La tabla en crudo: Es el archivo de entrada, registrado por el medidor.
   La tabla en procesado: Es el resultado del procesamiento del archivo crudo, generando una tabla con la estructura siguiente y nombres:
   **RÁFAGA_N, FECHA_HORA_DT, DISTANCIA_CM, TEMPERATURA_C, PRESION_ATM, HUMEDAD_PCT, DELTA_TD, DATOS_N**
   De estas, las variables secundarias son: RÁFAGA_N, DELTA_TD, DATOS_N; y son para un análisis de datos más técnico, relativo al medidor, y ocultas por defecto.
    
3. Sección gráfica
   Tras generar un gráfico, en su visualización, el ícono de una lupa permite seleccionar un rango dentro del gráfico para ampliar la visibilidad. El ícono de una casa es para
   recuperar las visualización inicial del gráfico
