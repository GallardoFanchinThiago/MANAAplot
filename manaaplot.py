import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.colorchooser as colorchooser

import pandas as pd
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import MaxNLocator


# --- 0. Variables globales para memoria y configuración ---

datos_memoria = {
    "crudo": None,
    "rafaga": None
}

configuracion_app = {
    "titulo_default": "Mi Gráfico",
    "mostrar_grid": True,
    "mostrar_leyenda": False,
    "redondeo_decimal": 2,
    "mostrar_secundarias": False
}

estado_grafico = {
    "color": "#0000FF",
    "tipo": "Línea",
    "col_x": None,
    "label_x": None,
    "rot_x": "0",
    "ticks_x": "0",
    "inv_x": False,
    "col_y": None,
    "label_y": None,
    "rot_y": "0",
    "ticks_y": "0",
    "inv_y": False
}

COLUMNAS_SECUNDARIAS = ("rafaga_n", "delta_td", "datos_n")
FUENTE_ETIQUETAS = ("gothic", 10)



def parse_float(valor, defecto=0.0):
    """Convierte a float de forma segura; devuelve `defecto` si no es válido."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def parse_ticks(valor):
    """Convierte a entero positivo (para nº de etiquetas); None si no aplica."""
    try:
        n = int(valor)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def cargaraw(raw):
    dfr = pd.read_csv(raw)
    dfr.columns = ["fecha_hora_dt", "distancia_cm", "temperatura_c",
                   "presion_atmosferica_hpa", "altitud_m", "humedad_pct"]

    dfr["fecha_hora_dt"] = pd.to_datetime(dfr["fecha_hora_dt"], dayfirst=True)

    dfr["distancia_cm"] = dfr["distancia_cm"].astype(int)
    columnas_float = dfr.columns[-4:]
    dfr[columnas_float] = dfr[columnas_float].astype(float)

    dfr = dfr.sort_values("fecha_hora_dt", ascending=True, ignore_index=True)
    dfr["delta_td"] = dfr["fecha_hora_dt"].diff().fillna(pd.Timedelta(0))
    dfr["rafaga_n"] = (dfr["delta_td"] > pd.Timedelta(1, "s")).cumsum()
    return dfr


def cargarafaga(burst):
    dfr = burst.copy()
    dfr["datos_n"] = dfr["rafaga_n"].copy()
    conteo = lambda x: x.count() if x.count() else np.nan
    moda_mediana = lambda x: x.mode().median() if not x.mode().empty else np.nan

    filtro = {
        "fecha_hora_dt": "min",
        "distancia_cm": moda_mediana,
        "temperatura_c": moda_mediana,
        "presion_atmosferica_hpa": moda_mediana,
        "altitud_m": moda_mediana,
        "humedad_pct": moda_mediana,
        "delta_td": "max",
        "datos_n": conteo
    }

    dfr = dfr.groupby("rafaga_n").agg(filtro).reset_index()
    return dfr


def mostrar_en_tabla(df):
    tree.delete(*tree.get_children())

    df_mostrar = df.copy()

    if not configuracion_app["mostrar_secundarias"]:
        columnas_a_eliminar = [c for c in COLUMNAS_SECUNDARIAS if c in df_mostrar.columns]
        if columnas_a_eliminar:
            df_mostrar = df_mostrar.drop(columns=columnas_a_eliminar)

    columnas_df = list(df_mostrar.columns)
    tree["columns"] = columnas_df
    for col in columnas_df:
        tree.heading(col, text=str(col).upper())
        tree.column(col, width=120, anchor='center')

    # Redondeo solo para visualización
    decimales = configuracion_app["redondeo_decimal"]
    columnas_float = df_mostrar.select_dtypes(include=['float64', 'float32']).columns
    if len(columnas_float):
        df_mostrar[columnas_float] = df_mostrar[columnas_float].round(decimales)

    for fila in df_mostrar.itertuples(index=False, name=None):
        tree.insert('', tk.END, values=fila)


def cargar_csv():
    var_estado.set("Esperando selección de archivo...")
    ruta_archivo = filedialog.askopenfilename(
        title="Selecciona un archivo CSV",
        filetypes=[("Archivos TXT", "*.txt"), ("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
    )
    if not ruta_archivo:
        var_estado.set("Carga cancelada. Listo.")
        return

    try:
        var_estado.set("Procesando archivo...")
        root.update()
        df = cargaraw(ruta_archivo)
        datos_memoria["crudo"] = df
        datos_memoria["rafaga"] = None

        var_transformacion.set("Crudo")
        mostrar_en_tabla(df)
        var_estado.set(f"Éxito: Archivo cargado ({len(df)} filas) -> {ruta_archivo}")
    except Exception as e:
        error_msg = f"Error al procesar: {e}"
        var_estado.set(error_msg)
        messagebox.showerror("Error", error_msg)


def cambiar_transformacion(seleccion):
    if datos_memoria["crudo"] is None:
        var_estado.set("Aviso: Primero debes cargar un archivo.")
        var_transformacion.set("Crudo")
        return
    try:
        if seleccion == "Ráfaga":
            var_estado.set("Calculando ráfagas...")
            root.update()
            if datos_memoria["rafaga"] is None:
                datos_memoria["rafaga"] = cargarafaga(datos_memoria["crudo"])
            mostrar_en_tabla(datos_memoria["rafaga"])
            var_estado.set(f"Éxito: Transformado a Ráfaga ({len(datos_memoria['rafaga'])} filas)")

        elif seleccion == "Crudo":
            var_estado.set("Cargando datos crudos...")
            root.update()
            mostrar_en_tabla(datos_memoria["crudo"])
            var_estado.set(f"Éxito: Mostrando datos Crudos ({len(datos_memoria['crudo'])} filas)")
    except Exception as e:
        error_msg = f"Error en la transformación: {e}"
        var_estado.set(error_msg)
        messagebox.showerror("Error", error_msg)


# --- FUNCIONES DE GRÁFICO ---
def crear_bloque_eje(parent, titulo_frame, columnas_disponibles,
                     clave_col, clave_label, clave_rot, clave_ticks, clave_inv,
                     indice_fallback=0):
    
    frame_eje = tk.LabelFrame(parent, text=titulo_frame, font=("gothic", 10, "bold"),
                               bg="#F0F0F0", padx=10, pady=10)
    frame_eje.pack(fill=tk.X, padx=15, pady=5)

    tk.Label(frame_eje, text="Columna de Datos:", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(anchor="w")

    valor_guardado = estado_grafico[clave_col]
    if valor_guardado in columnas_disponibles:
        def_col = valor_guardado
    else:
        idx = indice_fallback if indice_fallback < len(columnas_disponibles) else 0
        def_col = columnas_disponibles[idx]

    var_col = tk.StringVar(value=def_col)
    menu_col = tk.OptionMenu(frame_eje, var_col, *columnas_disponibles)
    menu_col.config(bg="#E0E0E0", font=FUENTE_ETIQUETAS, width=40)
    menu_col.pack(anchor="w", pady=(0, 10))

    tk.Label(frame_eje, text="Nombre del Eje:", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(anchor="w")
    def_label = estado_grafico[clave_label] if estado_grafico[clave_label] is not None else def_col
    var_label = tk.StringVar(value=def_label)
    tk.Entry(frame_eje, textvariable=var_label, font=FUENTE_ETIQUETAS, width=50).pack(anchor="w", pady=(0, 10))

    def actualizar_label(*_args):
        var_label.set(var_col.get())
    var_col.trace_add("write", actualizar_label)

    # --- NUEVO: Dividimos las opciones en dos filas (Frames) ---
    f_opts_top = tk.Frame(frame_eje, bg="#F0F0F0")
    f_opts_top.pack(fill=tk.X, pady=(0, 5))

    f_opts_bottom = tk.Frame(frame_eje, bg="#F0F0F0")
    f_opts_bottom.pack(fill=tk.X)

    # Fila 1: Inclinación y Nº de Etiquetas
    tk.Label(f_opts_top, text="Inclinación (°):", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(side=tk.LEFT)
    var_rot = tk.StringVar(value=estado_grafico[clave_rot])
    tk.Entry(f_opts_top, textvariable=var_rot, font=FUENTE_ETIQUETAS, width=5).pack(side=tk.LEFT, padx=5)

    tk.Label(f_opts_top, text="Nº Etiquetas (0=Auto):", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(side=tk.LEFT, padx=(15, 0))
    var_ticks = tk.StringVar(value=estado_grafico[clave_ticks])
    tk.Entry(f_opts_top, textvariable=var_ticks, font=FUENTE_ETIQUETAS, width=5).pack(side=tk.LEFT, padx=5)

    # Fila 2: Invertir eje
    var_inv = tk.BooleanVar(value=estado_grafico[clave_inv])
    tk.Checkbutton(f_opts_bottom, text="Invertir eje", variable=var_inv, bg="#F0F0F0",
                   font=FUENTE_ETIQUETAS).pack(side=tk.LEFT)

    return var_col, var_label, var_rot, var_ticks, var_inv


def abrir_config_grafico():
    if datos_memoria["crudo"] is None:
        messagebox.showwarning("Aviso", "Primero debes cargar un archivo de datos.")
        return

    estado_actual = var_transformacion.get()

    if estado_actual == "Crudo":
        respuesta = messagebox.askyesno(
            "Advertencia de Modo",
            "Este gráfico está pensado para el modo Ráfaga.\n\n¿Configurar gráfico igualmente?"
        )
        if not respuesta:
            return
        dfr = datos_memoria["crudo"]
    else:
        dfr = datos_memoria["rafaga"]

    columnas_disponibles = list(dfr.columns)

    if not configuracion_app["mostrar_secundarias"]:
        columnas_disponibles = [c for c in columnas_disponibles if c not in COLUMNAS_SECUNDARIAS]

    vent_conf = tk.Toplevel(root)
    vent_conf.title("Configuración del Gráfico")
    vent_conf.geometry("480x670")
    vent_conf.configure(bg="#F0F0F0")
    vent_conf.resizable(False, False)
    vent_conf.transient(root)
    vent_conf.grab_set()

    def elegir_color():
        color = colorchooser.askcolor(title="Elegir color")[1]
        if color:
            var_color.set(color)

    # --- APARTADO 1: GENERAL ---
    frame_general = tk.LabelFrame(vent_conf, text="General", font=("gothic", 10, "bold"),
                                   bg="#F0F0F0", padx=10, pady=10)
    frame_general.pack(fill=tk.X, padx=15, pady=5)

    tk.Label(frame_general, text="Título del Gráfico:", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(anchor="w")
    var_titulo = tk.StringVar(value=configuracion_app["titulo_default"])
    tk.Entry(frame_general, textvariable=var_titulo, font=FUENTE_ETIQUETAS, width=50).pack(anchor="w", pady=(0, 10))

    f_color = tk.Frame(frame_general, bg="#F0F0F0")
    f_color.pack(fill=tk.X)
    tk.Label(f_color, text="Color (Hex):", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(side=tk.LEFT)
    var_color = tk.StringVar(value=estado_grafico["color"])
    tk.Entry(f_color, textvariable=var_color, font=FUENTE_ETIQUETAS, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(f_color, text="Selector", font=("gothic", 9), command=elegir_color).pack(side=tk.LEFT)

    f_tipo = tk.Frame(frame_general, bg="#F0F0F0")
    f_tipo.pack(fill=tk.X, pady=(10, 0))
    tk.Label(f_tipo, text="Tipo de Gráfico:", bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(side=tk.LEFT)

    var_tipo_grafico = tk.StringVar(value=estado_grafico["tipo"])
    tk.Radiobutton(f_tipo, text="Línea", variable=var_tipo_grafico, value="Línea",
                   bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(side=tk.LEFT, padx=(5, 0))
    tk.Radiobutton(f_tipo, text="Dispersión", variable=var_tipo_grafico, value="Dispersión",
                   bg="#F0F0F0", font=FUENTE_ETIQUETAS).pack(side=tk.LEFT)

    # --- APARTADOS 2 y 3: VARIABLES X e Y (ahora vía función común) ---
    var_col_x, var_label_x, var_rot_x, var_ticks_x, var_inv_x = crear_bloque_eje(
        vent_conf, "Variable X (Eje Horizontal)", columnas_disponibles,
        "col_x", "label_x", "rot_x", "ticks_x", "inv_x", indice_fallback=0
    )
    var_col_y, var_label_y, var_rot_y, var_ticks_y, var_inv_y = crear_bloque_eje(
        vent_conf, "Variable Y (Eje Vertical)", columnas_disponibles,
        "col_y", "label_y", "rot_y", "ticks_y", "inv_y", indice_fallback=1
    )

    # --- BOTÓN DE GENERAR ---
    btn_generar = tk.Button(
        vent_conf, text="Generar Gráfico",
        command=lambda: generar_grafico_personalizado(
            dfr, var_col_x.get(), var_col_y.get(), var_titulo.get(),
            var_label_x.get(), var_label_y.get(), var_color.get(),
            var_rot_x.get(), var_ticks_x.get(), var_inv_x.get(),
            var_rot_y.get(), var_ticks_y.get(), var_inv_y.get(),
            var_tipo_grafico.get(),
            vent_conf
        ),
        relief=tk.FLAT, highlightthickness=2, highlightbackground='#999999',
        font=("gothic", 11, "bold"), bg="#D0D0D0", pady=5
    )
    btn_generar.pack(fill=tk.X, padx=15, pady=15)


def generar_grafico_personalizado(dfr, col_x, col_y, titulo, label_x, label_y, color_hex,
                                   rot_x, ticks_x, inv_x, rot_y, ticks_y, inv_y,
                                   tipo_grafico, vent_padre):
    
    estado_grafico.update({
        "color": color_hex,
        "tipo": tipo_grafico,
        "col_x": col_x,
        "label_x": label_x,
        "rot_x": rot_x,
        "ticks_x": ticks_x,
        "inv_x": inv_x,
        "col_y": col_y,
        "label_y": label_y,
        "rot_y": rot_y,
        "ticks_y": ticks_y,
        "inv_y": inv_y
    })

    try:
        vent_padre.destroy()
        var_estado.set(f"Generando gráfico: {col_y} vs {col_x}...")
        root.update()

        ventana_graf = tk.Toplevel(root)
        ventana_graf.title(f"Gráfico: {titulo}")
        ventana_graf.geometry("850x600")
        ventana_graf.configure(bg="#F0F0F0")

        fig = Figure(figsize=(16 * 2 / 3, 9 * 2 / 3), dpi=100)
        ax = fig.add_subplot(111)

        t = dfr[col_x]
        h = dfr[col_y]

        if tipo_grafico == "Dispersión":
            ax.scatter(t, h, color=color_hex, s=15, alpha=0.8)
        else:
            ax.plot(t, h, linewidth=0.5, color=color_hex)

        ax.set_xlabel(label_x)
        ax.set_ylabel(label_y)
        ax.set_title(titulo)

        ax.tick_params(axis='x', rotation=parse_float(rot_x, 0))
        ax.tick_params(axis='y', rotation=parse_float(rot_y, 0))

        n_ticks_x = parse_ticks(ticks_x)
        if n_ticks_x:
            ax.xaxis.set_major_locator(MaxNLocator(n_ticks_x))

        n_ticks_y = parse_ticks(ticks_y)
        if n_ticks_y:
            ax.yaxis.set_major_locator(MaxNLocator(n_ticks_y))

        if inv_x:
            ax.invert_xaxis()
        if inv_y:
            ax.invert_yaxis()

        if configuracion_app["mostrar_grid"]:
            ax.grid(True, axis="both", linewidth=0.5, linestyle="--")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=ventana_graf)
        canvas.draw()

        toolbar_frame = tk.Frame(ventana_graf, bg="#F0F0F0")
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        var_estado.set("Gráfico generado con éxito.")

    except Exception as e:
        error_msg = f"Error al graficar (revisa el Color o los Datos): {e}"
        var_estado.set(error_msg)
        messagebox.showerror("Error de Gráfico", error_msg)


# --- PROPIEDADES ---
def abrir_propiedades():
    ventana_prop = tk.Toplevel(root)
    ventana_prop.title("Propiedades")
    ventana_prop.geometry("320x360")
    ventana_prop.configure(bg="#F0F0F0")
    ventana_prop.resizable(False, False)
    ventana_prop.transient(root)
    ventana_prop.grab_set()

    marco_opciones = tk.Frame(ventana_prop, bg="#F0F0F0", padx=20, pady=15)
    marco_opciones.pack(fill=tk.BOTH, expand=True)

    tk.Label(marco_opciones, text="Preferencias Globales", font=("Arial", 11, "bold"),
             bg="#F0F0F0").pack(anchor="w", pady=(0, 10))

    tk.Label(marco_opciones, text="Título por defecto:", bg="#F0F0F0", font=("Arial", 10)).pack(anchor="w")
    var_tit_def = tk.StringVar(value=configuracion_app["titulo_default"])
    tk.Entry(marco_opciones, textvariable=var_tit_def, width=30).pack(anchor="w", pady=(0, 10))

    var_grid = tk.BooleanVar(value=configuracion_app["mostrar_grid"])
    tk.Checkbutton(marco_opciones, text="Mostrar cuadrícula (Grid)", variable=var_grid,
                   bg="#F0F0F0", font=("Arial", 10)).pack(anchor="w", pady=2)

    var_leyenda = tk.BooleanVar(value=configuracion_app["mostrar_leyenda"])
    tk.Checkbutton(marco_opciones, text="Mostrar leyenda", variable=var_leyenda,
                   bg="#F0F0F0", font=("Arial", 10)).pack(anchor="w", pady=2)

    var_secundarias = tk.BooleanVar(value=configuracion_app["mostrar_secundarias"])
    tk.Checkbutton(marco_opciones, text="Mostrar variables secundarias", variable=var_secundarias,
                   bg="#F0F0F0", font=("Arial", 10)).pack(anchor="w", pady=2)

    f_redondeo = tk.Frame(marco_opciones, bg="#F0F0F0")
    f_redondeo.pack(fill=tk.X, pady=(10, 0))
    tk.Label(f_redondeo, text="Decimales a mostrar:", bg="#F0F0F0", font=("Arial", 10)).pack(side=tk.LEFT)
    var_redondeo = tk.IntVar(value=configuracion_app["redondeo_decimal"])
    tk.Spinbox(f_redondeo, from_=0, to=8, textvariable=var_redondeo, width=5, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

    ttk.Separator(marco_opciones, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

    def guardar_propiedades():
        configuracion_app.update({
            "titulo_default": var_tit_def.get(),
            "mostrar_grid": var_grid.get(),
            "mostrar_leyenda": var_leyenda.get(),
            "redondeo_decimal": var_redondeo.get(),
            "mostrar_secundarias": var_secundarias.get()
        })

        estado_actual = var_transformacion.get()
        if estado_actual == "Crudo" and datos_memoria["crudo"] is not None:
            mostrar_en_tabla(datos_memoria["crudo"])
        elif estado_actual == "Ráfaga" and datos_memoria["rafaga"] is not None:
            mostrar_en_tabla(datos_memoria["rafaga"])

        ventana_prop.destroy()

    btn_aceptar = tk.Button(
        marco_opciones, text="Aceptar", command=guardar_propiedades,
        relief=tk.FLAT, highlightthickness=2, highlightbackground='#999999', width=10, bg="#E0E0E0"
    )
    btn_aceptar.pack(side=tk.BOTTOM)

# CREACIÓN DE LA INTERFAZ PRINCIPAL
root = tk.Tk()
root.title("MANAAplot v0.2 alpha")
root.geometry("800x600")
root.configure(bg="#F0F0F0")

style = ttk.Style()
style.theme_use('classic')
style.configure("Treeview.Heading", font=("gothic", 10, "bold"), background="#CCCCCC", relief=tk.RAISED)
style.configure("Treeview", font=("gothic", 10), rowheight=20)
style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

button_frame = tk.Frame(root, bg="#F0F0F0")
button_frame.pack(fill=tk.X, padx=10, pady=(5, 10), side=tk.BOTTOM)

btn_opts = {
    'relief': tk.FLAT, 'highlightthickness': 2, 'highlightbackground': '#999999',
    'font': ("gothic", 11), 'width': 15, 'bg': "#E0E0E0", 'activebackground': "#CCCCCC"
}

btn3 = tk.Button(button_frame, text="Propiedades", command=abrir_propiedades, **btn_opts)
btn3.pack(side=tk.LEFT, padx=(10, 0))

btn2 = tk.Button(button_frame, text="Elegir archivo", command=cargar_csv, **btn_opts)
btn2.pack(side=tk.LEFT, padx=(10, 0))

var_transformacion = tk.StringVar(value="Crudo")
opciones_transformacion = ["Crudo", "Ráfaga"]

menu_transformar = tk.OptionMenu(button_frame, var_transformacion, *opciones_transformacion, command=cambiar_transformacion)
menu_transformar.config(
    relief=tk.FLAT, highlightthickness=2, highlightbackground='#999999',
    font=("gothic", 11), bg="#E0E0E0", activebackground="#CCCCCC", width=13
)
menu_transformar["menu"].config(bg="#E0E0E0", font=("gothic", 11))
menu_transformar.pack(side=tk.LEFT, padx=(10, 0))

btn1 = tk.Button(button_frame, text="Nuevo gráfico", command=abrir_config_grafico, **btn_opts)
btn1.pack(side=tk.LEFT, padx=(10, 0))

var_estado = tk.StringVar()
var_estado.set("Listo. Esperando datos...")

status_label = tk.Label(root, textvariable=var_estado, anchor="w", font=("gothic", 10),
                         bg="#E0E0E0", fg="black", bd=2, relief=tk.SUNKEN)
status_label.pack(fill=tk.X, padx=10, pady=(0, 5), side=tk.BOTTOM)

data_frame = tk.Frame(root, bd=2, relief=tk.SUNKEN, bg="#E0E0E0")
data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

tree_container = tk.Frame(data_frame, bg="white")
tree_container.pack(fill=tk.BOTH, expand=True)

columnas_iniciales = ('c1', 'c2', 'c3', 'c4', 'c5', 'c6')
tree = ttk.Treeview(tree_container, columns=columnas_iniciales, show='headings')

for col in columnas_iniciales:
    tree.heading(col, text="")
    tree.column(col, width=60, anchor='center')

scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

h_scrollbar = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL, command=tree.xview)
tree.configure(xscrollcommand=h_scrollbar.set)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

for _ in range(25):
    tree.insert('', tk.END, values=('', '', '', '', '', ''))

root.mainloop()
