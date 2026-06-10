import pygame.midi
import pygame
import time
import os
import sys


# Install bei geänderten Sounds:
#pyinstaller --noconsole --onefile --add-data "wav;wav" _LDP8PadFire_2.02_mitGUI.py


# --- KONFIGURATION ---
TARGET_DEVICE_NAME = "LPD8 mk2"  # Hier den Namen deines Wunschgeräts eintragen
# ---------------------

# Errechnet den Pfad zur Ressource (für PyInstaller oder lokale Ausführung)
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # Wenn wir als EXE laufen, nutze den temporären Entpack-Ordner
        return os.path.join(sys._MEIPASS, relative_path)
    # Wenn wir als normales Skript laufen, nutze den normalen Pfad
    return os.path.join(os.path.abspath("."), relative_path)

# Initialisiere Pygame MIDI und Mixer
pygame.midi.init()
pygame.mixer.init()

# Setze die Fenstergröße und initialisiere Pygame Display
pygame.init()
screen = pygame.display.set_mode((250, 110))
pygame.display.set_caption(f'Pad Fire - {TARGET_DEVICE_NAME}')

# Farben definieren
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
BLACK = (80, 0, 0)

# Schriftart initialisieren
pygame.font.init()
font = pygame.font.SysFont(None, 12)

# Lade die WAV-Dateien für jedes Pad mit Fehlerbehandlung
sounds = {}
pad_notes = [36, 37, 38, 39, 40, 41, 42, 43]
for note in pad_notes:
    try:
        # Hier wird die magische Funktion genutzt:
        path = resource_path(f'wav/sound{note - 35}.wav')
        sounds[note] = pygame.mixer.Sound(path)
    except pygame.error as e:
        print(f"Fehler beim Laden von {path}: {e}")

# Pad-Positionen und -Größen
pad_positions = {
    36: pygame.Rect(10, 60, 50, 40),
    37: pygame.Rect(70, 60, 50, 40),
    38: pygame.Rect(130, 60, 50, 40),
    39: pygame.Rect(190, 60, 50, 40),
    40: pygame.Rect(10, 10, 50, 40),
    41: pygame.Rect(70, 10, 50, 40),
    42: pygame.Rect(130, 10, 50, 40),
    43: pygame.Rect(190, 10, 50, 40)
}

# Zuordnung von Labels
pad_labels = {
    36: "1- Applaus", 37: "2- Pause", 38: "3- MiniIntro", 39: "4- Alarm",
    40: "5- Klatschen", 41: "6- BigIntro", 42: "7- Correct", 43: "8- Wrong"
}

active_pads = set()

def find_device_id(name_filter):
    """Sucht die ID eines Eingabegeräts basierend auf dem Namen."""
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        # info[1] ist der Name, info[2] ist 1 bei Input-Geräten
        if name_filter.lower() in info[1].decode().lower() and info[2] == 1:
            return i
    return None

# MIDI-Gerät dynamisch suchen
target_id = find_device_id(TARGET_DEVICE_NAME)

if target_id is not None:
    try:
        input_device = pygame.midi.Input(target_id)
        print(f"Verbunden mit: {pygame.midi.get_device_info(target_id)[1].decode()} (ID: {target_id})")
    except Exception as e:
        print(f"Fehler beim Öffnen des MIDI-Geräts: {e}")
        pygame.quit()
        exit()
else:
    print(f"Gerät '{TARGET_DEVICE_NAME}' nicht gefunden!")
    print("Verfügbare Eingänge:")
    for i in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(i)
        if info[2] == 1: print(f"- {info[1].decode()}")
    pygame.quit()
    exit()

def draw_text(text, rect, color=BLACK):
    label = font.render(text, True, color)
    text_rect = label.get_rect(center=rect.center)
    screen.blit(label, text_rect)

def draw_pads():
    screen.fill(WHITE)
    for note, rect in pad_positions.items():
        color = GREEN if note in active_pads else GRAY
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        draw_text(pad_labels[note], rect)
    pygame.display.flip()

def trigger_pad(note):
    if note in sounds:
        sounds[note].play()
        active_pads.add(note)

def handle_mouse_click(pos):
    for note, rect in pad_positions.items():
        if rect.collidepoint(pos):
            active_pads.add(note)
            trigger_pad(note)
            # Hinweis: In einer echten App wäre ein Timer besser als sleep, 
            # aber für ein einfaches Tool funktioniert es.
            time.sleep(0.1) 
            active_pads.remove(note)

# Hauptschleife
clock = pygame.time.Clock()
try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_click(event.pos)

        # MIDI-Events abfragen
        if input_device.poll():
            midi_events = input_device.read(10)
            for event in midi_events:
                status = event[0][0]
                note = event[0][1]
                velocity = event[0][2]

                # Note-On (153 = Kanal 10, 144 = Kanal 1)
                # Da viele Keyboards auf Kanal 1 senden, prüfen wir hier 
                # flexibel auf Note-On Statusmeldungen (144-159)
                if 144 <= status <= 159 and velocity > 0:
                    trigger_pad(note)
                # Note-Off (128-143) oder Note-On mit Velocity 0
                elif (128 <= status <= 143) or (144 <= status <= 159 and velocity == 0):
                    if note in active_pads:
                        active_pads.remove(note)

        draw_pads()
        clock.tick(30)

except KeyboardInterrupt:
    print("Programm beendet")

finally:
    input_device.close()
    pygame.midi.quit()
    pygame.quit()