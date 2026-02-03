"""Juego de fútbol modo carrera con interfaz gráfica básica (Tkinter)."""

from __future__ import annotations

import json
import random
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import messagebox

SAVE_PATH = Path("savegame.json")


def clamp(value: int, min_value: int = 1, max_value: int = 99) -> int:
    """Asegura que un valor quede en un rango."""
    return max(min_value, min(max_value, value))


@dataclass
class PlayerStats:
    """Atributos extendidos del jugador."""

    # Físicos
    velocidad: int
    fuerza: int
    resistencia: int

    # Técnicos
    pase: int
    tiro: int
    control: int
    regate: int

    # Mentales
    liderazgo: int
    agresividad: int
    compostura: int

    # Emocionales
    confianza: int
    presion: int
    motivacion: int

    def promedio(self) -> int:
        valores = list(asdict(self).values())
        return int(sum(valores) / len(valores))


@dataclass
class Player:
    """Representa al jugador creado por el usuario."""

    nombre: str
    posicion: str
    stats: PlayerStats
    partidos: int = 0
    goles: int = 0
    asistencias: int = 0
    valoracion_general: int = 50
    fatiga: int = 0

    def actualizar_valoracion(self) -> None:
        """Actualiza la valoración general basándose en stats y rendimiento."""
        base = self.stats.promedio()
        bonus = min(10, self.goles + self.asistencias)
        penalty = int(self.fatiga / 10)
        self.valoracion_general = clamp(base + bonus - penalty)

    def entrenar(self, enfoque: str) -> None:
        """Permite mejorar estadísticas según el enfoque."""
        mejoras = {
            "fisico": ["velocidad", "fuerza", "resistencia"],
            "tecnico": ["pase", "tiro", "control", "regate"],
            "mental": ["liderazgo", "agresividad", "compostura"],
            "emocional": ["confianza", "presion", "motivacion"],
        }
        for atributo in mejoras.get(enfoque, []):
            actual = getattr(self.stats, atributo)
            setattr(self.stats, atributo, clamp(actual + random.randint(1, 3)))
        self.fatiga = clamp(self.fatiga + 8, 0, 100)
        self.actualizar_valoracion()


@dataclass
class Team:
    """Representa un equipo de fútbol."""

    nombre: str
    nivel: int
    presupuesto: int
    entrenador: str
    tactica: str
    confianza: int = 50

    def rating(self) -> int:
        """Rating del equipo considerando nivel y confianza."""
        return clamp(int(self.nivel + (self.confianza - 50) / 2))


@dataclass
class SeasonStats:
    """Estadísticas acumuladas por temporada."""

    temporada: int
    partidos: int = 0
    goles: int = 0
    asistencias: int = 0
    logros: list[str] = field(default_factory=list)


@dataclass
class CareerState:
    """Estado global del modo carrera."""

    jugador: Player
    equipo: Team
    temporada: int = 1
    historial: list[SeasonStats] = field(default_factory=list)
    modo: str = "Carrera de jugador"
    reputacion: int = 50

    def temporada_actual(self) -> SeasonStats:
        for item in self.historial:
            if item.temporada == self.temporada:
                return item
        nueva = SeasonStats(temporada=self.temporada)
        self.historial.append(nueva)
        return nueva


def crear_equipo_inicial() -> Team:
    """Crea un equipo modesto."""
    return Team(
        nombre="Atlético Barrio",
        nivel=55,
        presupuesto=500_000,
        entrenador="Marta Ríos",
        tactica="4-4-2",
    )


def crear_equipo_oferta(reputacion: int) -> Team:
    """Genera un equipo de mejor nivel para ofertas de fichajes."""
    base = clamp(55 + int(reputacion / 2))
    return Team(
        nombre=random.choice(["CD Aurora", "Real Montaña", "Unión Capital", "Rayo Sur"]),
        nivel=clamp(base + random.randint(0, 12)),
        presupuesto=random.randint(800_000, 2_000_000),
        entrenador=random.choice(["L. Serrano", "Paula Costa", "J. Vega", "N. Paredes"]),
        tactica=random.choice(["4-3-3", "3-5-2", "4-2-3-1"]),
    )


def simular_partido(estado: CareerState, rival: Team) -> str:
    """Simula un partido y devuelve un resumen de eventos.

    Cada segundo/minuto del partido se calcula con probabilidades basadas
    en estadísticas y contexto. Para mantener el rendimiento, se simula
    con 90 ticks representando minutos de partido.
    """

    jugador = estado.jugador
    equipo = estado.equipo
    resumen = []
    goles_local = 0
    goles_rival = 0

    # Ajustes por fatiga, tácticas y estado emocional
    ventaja_local = (
        jugador.stats.confianza - jugador.stats.presion + jugador.stats.motivacion
    ) / 30
    fatiga_penalty = jugador.fatiga / 100

    for minuto in range(1, 91):
        # Sistema de fatiga
        jugador.fatiga = clamp(jugador.fatiga + random.randint(0, 2), 0, 100)

        # Eventos aleatorios: clima, lesiones, rebotes
        evento_random = random.random()
        if evento_random < 0.02:
            resumen.append(f"Min {minuto}: Clima pesado reduce ritmo.")
            fatiga_penalty += 0.02
        elif evento_random < 0.04:
            resumen.append(f"Min {minuto}: Rebote inesperado cerca del área.")

        # IA adaptativa: rival ajusta táctica si pierde
        ia_boost = 0
        if goles_rival < goles_local and minuto > 60:
            ia_boost = 2
            resumen.append(f"Min {minuto}: {rival.nombre} ajusta su táctica.")

        # Probabilidad de gol basada en ratings
        rating_local = equipo.rating() + jugador.valoracion_general / 2
        rating_rival = rival.rating() + ia_boost
        prob_local = (rating_local - rating_rival + ventaja_local * 10) / 200
        prob_rival = (rating_rival - rating_local + 10) / 220
        prob_local = max(0.01, prob_local - fatiga_penalty)
        prob_rival = max(0.01, prob_rival + fatiga_penalty / 2)

        if random.random() < prob_local:
            goles_local += 1
            jugador.goles += 1
            resumen.append(f"Min {minuto}: ¡Gol de {jugador.nombre}!")
        if random.random() < prob_rival:
            goles_rival += 1
            resumen.append(f"Min {minuto}: Gol de {rival.nombre}.")

    jugador.partidos += 1
    jugador.asistencias += random.randint(0, 1)
    jugador.actualizar_valoracion()
    estado.temporada_actual().partidos += 1
    estado.temporada_actual().goles += jugador.goles
    estado.temporada_actual().asistencias += jugador.asistencias

    resultado = f"Resultado: {equipo.nombre} {goles_local} - {goles_rival} {rival.nombre}"
    resumen.append(resultado)
    estado.reputacion = clamp(estado.reputacion + (goles_local - goles_rival) * 2, 1, 100)
    equipo.confianza = clamp(equipo.confianza + (goles_local - goles_rival) * 3, 1, 99)
    return "\n".join(resumen[-8:])


def mercado_fichajes(estado: CareerState) -> str:
    """Genera una oferta de fichaje y permite aceptar o rechazar."""
    oferta = crear_equipo_oferta(estado.reputacion)
    return (
        f"Oferta de {oferta.nombre} (nivel {oferta.nivel}). "
        f"Entrenador: {oferta.entrenador}. Táctica: {oferta.tactica}."
    )


def premios_temporada(estado: CareerState) -> list[str]:
    """Determina premios y logros de temporada."""
    premios = [
        "Balón de Oro",
        "The Best",
        "Puskás",
        "Yashin",
        "Mejor Entrenador",
        "Rey de América",
        "Balón de Oro Latino",
        "Mejor jugador Libertadores",
        "Mejor XI del año",
    ]
    ganados = []
    rating = estado.jugador.valoracion_general
    for premio in premios:
        if random.random() < rating / 200:
            ganados.append(premio)
    if not ganados:
        ganados.append("Reconocimiento local")
    return ganados


def guardar_partida(estado: CareerState) -> None:
    """Guarda el progreso en un archivo JSON."""
    data = asdict(estado)
    SAVE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def cargar_partida() -> CareerState | None:
    """Carga el progreso desde un archivo JSON."""
    if not SAVE_PATH.exists():
        return None
    data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    jugador_stats = PlayerStats(**data["jugador"]["stats"])
    jugador = Player(**{**data["jugador"], "stats": jugador_stats})
    equipo = Team(**data["equipo"])
    historial = [SeasonStats(**item) for item in data.get("historial", [])]
    return CareerState(
        jugador=jugador,
        equipo=equipo,
        temporada=data.get("temporada", 1),
        historial=historial,
        modo=data.get("modo", "Carrera de jugador"),
        reputacion=data.get("reputacion", 50),
    )


class CareerApp:
    """Interfaz principal del juego."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Modo Carrera - Fútbol")
        self.estado: CareerState | None = None

        self.texto = tk.Text(root, width=80, height=24, bg="#0b1320", fg="#e0e0e0")
        self.texto.pack(padx=10, pady=10)

        self.botones = tk.Frame(root)
        self.botones.pack(pady=4)

        self.btn_nuevo = tk.Button(self.botones, text="Nueva carrera", command=self.nueva_carrera)
        self.btn_cargar = tk.Button(self.botones, text="Cargar partida", command=self.cargar)
        self.btn_guardar = tk.Button(self.botones, text="Guardar", command=self.guardar)
        self.btn_jugar = tk.Button(self.botones, text="Jugar partido", command=self.jugar)
        self.btn_entrenar = tk.Button(self.botones, text="Entrenar", command=self.entrenar)
        self.btn_mercado = tk.Button(self.botones, text="Mercado", command=self.mercado)
        self.btn_stats = tk.Button(self.botones, text="Estadísticas", command=self.mostrar_stats)
        self.btn_temp = tk.Button(self.botones, text="Cerrar temporada", command=self.cerrar_temporada)
        self.btn_salir = tk.Button(self.botones, text="Salir", command=root.quit)

        for widget in [
            self.btn_nuevo,
            self.btn_cargar,
            self.btn_guardar,
            self.btn_jugar,
            self.btn_entrenar,
            self.btn_mercado,
            self.btn_stats,
            self.btn_temp,
            self.btn_salir,
        ]:
            widget.pack(side=tk.LEFT, padx=4)

        self.mostrar_carga()

    def mostrar_carga(self) -> None:
        """Pantalla inicial de carga."""
        self.texto.delete("1.0", tk.END)
        self.texto.insert(
            tk.END,
            "Cargando motor de partido...\n"
            "Inicializando narrativa y árbol de decisiones...\n"
            "Listo para iniciar tu carrera.\n",
        )

    def nueva_carrera(self) -> None:
        """Flujo de creación de jugador y carrera."""
        nombre = simple_input(self.root, "Nombre del jugador")
        if not nombre:
            return
        posicion = simple_input(self.root, "Posición (delantero, mediocampista, defensa)")
        stats = PlayerStats(
            velocidad=random.randint(50, 70),
            fuerza=random.randint(45, 65),
            resistencia=random.randint(50, 70),
            pase=random.randint(45, 65),
            tiro=random.randint(50, 70),
            control=random.randint(45, 65),
            regate=random.randint(45, 65),
            liderazgo=random.randint(40, 60),
            agresividad=random.randint(40, 60),
            compostura=random.randint(40, 60),
            confianza=random.randint(45, 65),
            presion=random.randint(40, 60),
            motivacion=random.randint(45, 65),
        )
        jugador = Player(nombre=nombre, posicion=posicion, stats=stats)
        jugador.actualizar_valoracion()
        equipo = crear_equipo_inicial()
        self.estado = CareerState(jugador=jugador, equipo=equipo)
        self.log(
            f"Bienvenido {jugador.nombre}. Inicias en {equipo.nombre} con táctica {equipo.tactica}."
        )

    def cargar(self) -> None:
        estado = cargar_partida()
        if not estado:
            messagebox.showinfo("Cargar", "No hay partida guardada.")
            return
        self.estado = estado
        self.log("Partida cargada correctamente.")

    def guardar(self) -> None:
        if not self.estado:
            messagebox.showwarning("Guardar", "No hay carrera activa.")
            return
        guardar_partida(self.estado)
        self.log("Partida guardada.")

    def jugar(self) -> None:
        if not self.estado:
            messagebox.showwarning("Partido", "Primero inicia una carrera.")
            return
        rival = crear_equipo_oferta(random.randint(40, 80))
        resumen = simular_partido(self.estado, rival)
        self.log(resumen)

    def entrenar(self) -> None:
        if not self.estado:
            return
        enfoque = simple_input(self.root, "Entrenamiento (fisico, tecnico, mental, emocional)")
        if not enfoque:
            return
        self.estado.jugador.entrenar(enfoque.lower())
        self.log("Entrenamiento completado. Estadísticas mejoradas.")

    def mercado(self) -> None:
        if not self.estado:
            return
        oferta_texto = mercado_fichajes(self.estado)
        aceptar = messagebox.askyesno("Mercado", f"{oferta_texto}\n¿Aceptar oferta?")
        if aceptar:
            nueva = crear_equipo_oferta(self.estado.reputacion)
            self.estado.equipo = nueva
            self.log(f"Fichado por {nueva.nombre}. Nueva etapa iniciada.")
        else:
            self.log("Oferta rechazada. Continúas en tu equipo actual.")

    def mostrar_stats(self) -> None:
        if not self.estado:
            return
        jugador = self.estado.jugador
        self.log(
            "\n".join(
                [
                    f"Jugador: {jugador.nombre}",
                    f"Posición: {jugador.posicion}",
                    f"Partidos: {jugador.partidos}",
                    f"Goles: {jugador.goles}",
                    f"Asistencias: {jugador.asistencias}",
                    f"Valoración general: {jugador.valoracion_general}",
                ]
            )
        )

    def cerrar_temporada(self) -> None:
        if not self.estado:
            return
        logros = premios_temporada(self.estado)
        temporada = self.estado.temporada_actual()
        temporada.logros.extend(logros)
        self.estado.temporada += 1
        self.log(
            "Temporada cerrada. Premios obtenidos:\n" + "\n".join(f"- {x}" for x in logros)
        )

    def log(self, mensaje: str) -> None:
        """Imprime mensajes en la interfaz."""
        self.texto.insert(tk.END, f"\n{mensaje}\n")
        self.texto.see(tk.END)


def simple_input(root: tk.Tk, prompt: str) -> str:
    """Crea un cuadro de entrada sencillo para capturar texto."""
    ventana = tk.Toplevel(root)
    ventana.title("Entrada")
    tk.Label(ventana, text=prompt).pack(padx=10, pady=6)
    entrada = tk.Entry(ventana)
    entrada.pack(padx=10, pady=6)
    entrada.focus_set()

    valor = {"texto": ""}

    def aceptar() -> None:
        valor["texto"] = entrada.get().strip()
        ventana.destroy()

    tk.Button(ventana, text="Aceptar", command=aceptar).pack(pady=6)
    ventana.wait_window()
    return valor["texto"]


def main() -> None:
    """Punto de entrada del juego."""
    root = tk.Tk()
    app = CareerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
