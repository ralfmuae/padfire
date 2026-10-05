import mido
import pygame
import time
import os
import sys

# Pygame-Backend for mido
mido.set_backend('mido.backends.pygame')

# Install help - for PyInstaller:
# pip install pyinstaller
# pyinstaller --noconsole --onefile --hidden-import=mido.backends.pygame --add-data "wav;wav" _LDP8PadFire_2.04.py

# --- Set target device ---
TARGET_DEVICE_NAME = "LPD8 mk2"
# ---------------------

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Initialising Pygame
pygame.mixer.init()
pygame.init()
screen = pygame.display.set_mode((250, 110))
pygame.display.set_caption(f'Pad Fire - {TARGET_DEVICE_NAME}')

WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
BLACK = (80, 0, 0)
RED = (255, 0, 0)    

pygame.font.init()
font = pygame.font.SysFont(None, 12)

# Noten-Definitionen
pad_notes = [36, 37, 38, 39, 40, 41, 42, 43]

# Dictionary for valume (0 to 127) for each pad (Standard: Max / 127)
pad_volumes = {note: 50 for note in pad_notes}

# load sounds 
sounds = {}
for note in pad_notes:
    path = resource_path(f'wav/sound{note - 35}.wav')
    try:
        sounds[note] = pygame.mixer.Sound(path)
        sounds[note].set_volume(0.4)
    except pygame.error as e:
        print(f"Error loading {path}: {e}")

# Pad-Positions (GUI)
pad_positions = {
    36: pygame.Rect(10, 60, 50, 40), 37: pygame.Rect(70, 60, 50, 40),
    38: pygame.Rect(130, 60, 50, 40), 39: pygame.Rect(190, 60, 50, 40),
    40: pygame.Rect(10, 10, 50, 40), 41: pygame.Rect(70, 10, 50, 40),
    42: pygame.Rect(130, 10, 50, 40), 43: pygame.Rect(190, 10, 50, 40)
}

pad_labels = {
    36: "1 Applaus", 
    37: "2 Pause", 
    38: "3 MinIntro", 
    39: "4 Alarm",
    40: "5 Claps", 
    41: "6 BigIntro", 
    42: "7 true", 
    43: "8 false"
}

# Mapping: 
cc_to_note_mapping = {
    70: 40, 71: 41, 72: 42, 73: 43,  # upper row 
    74: 36, 75: 37, 76: 38, 77: 39   # lower row
}

active_pads = set()
midi_out = None

def find_mido_ports(name_filter):
    # using native pygame.midi, for background query 
    import pygame.midi
    if not pygame.midi.get_init():
        pygame.midi.init()
    
    in_port = None
    out_port = None
    
    # runthrough, no touching the ports
    for i in range(pygame.midi.get_count()):
        interf, name, is_input, is_output, opened = pygame.midi.get_device_info(i)
        device_name = name.decode('utf-8', errors='ignore')
        
        if name_filter.lower() in device_name.lower():
            if is_input and not in_port:
                # mido needs the exact name
                in_port = device_name
            if is_output and not out_port:
                out_port = device_name
                
    return in_port, out_port

# search midi devices via mido
in_name, out_name = find_mido_ports(TARGET_DEVICE_NAME)

if in_name:
    try:
        midi_in = mido.open_input(in_name)
        print(f"Connnected to: {in_name}")
        if out_name:
            midi_out = mido.open_output(out_name)
    except Exception as e:
        print(f"Error opening: {e}")
        pygame.quit()
        exit()
else:
    # --- Device not found: visual warning ---
    print(f"Device '{TARGET_DEVICE_NAME}' not found!")
    
    # Warn message
    waiting_for_exit = True
    font_large = pygame.font.SysFont(None, 16) # Bigger font for warning
    
    while waiting_for_exit:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                waiting_for_exit = False
                
        screen.fill(WHITE)
        # draw warning
        pygame.draw.rect(screen, RED, (10, 10, 230, 90), 3)
        
        # generate message
        lbl1 = font_large.render("Error: no controller!", True, RED)
        lbl2 = font.render(f"'{TARGET_DEVICE_NAME}' not found.", True, BLACK)
        lbl3 = font.render("Check cables & start new.", True, BLACK)
        
        # place it
        screen.blit(lbl1, lbl1.get_rect(centerx=125, top=25))
        screen.blit(lbl2, lbl2.get_rect(centerx=125, top=50))
        screen.blit(lbl3, lbl3.get_rect(centerx=125, top=70))
        
        pygame.display.flip()
        pygame.time.Clock().tick(15)
        
    pygame.quit()
    exit()


def draw_multiline_text(text1, text2, rect, color=BLACK):
    
    label1 = font.render(text1, True, color)
    label2 = font.render(text2, True, color)
    
    # calculate placing
    total_height = label1.get_height() + label2.get_height() + 4
    
    # calculate start-y-position
    start_y = rect.y + (rect.height - total_height) // 2
    
    # first row centered
    text_rect1 = label1.get_rect(centerx=rect.centerx, top=start_y)
    # 2nd row
    text_rect2 = label2.get_rect(centerx=rect.centerx, top=text_rect1.bottom + 4)
    
    screen.blit(label1, text_rect1)
    screen.blit(label2, text_rect2)

def draw_pads():
    screen.fill(WHITE)
    for note, rect in pad_positions.items():
        color = GREEN if note in active_pads else GRAY
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        
        # calculate value (0-100)
        vol_percent = int((pad_volumes[note] / 127) * 100)
        
        # Row 1: Name ("1- Applaus")
        line1 = pad_labels[note]
        # Row 2: Volume ("Vol: 85%")
        line2 = f"Vol: {vol_percent}%"
        
        # dynamic color: if  red under 10%, else black
        text_color = RED if vol_percent < 10 else BLACK
        
        # draw text
        draw_multiline_text(line1, line2, rect, text_color)
        
    pygame.display.flip()

def trigger_pad_on(note):
    if note in sounds:
        pygame_vol = pad_volumes[note] / 127.0
        sounds[note].set_volume(pygame_vol)
        sounds[note].play()
    active_pads.add(note)
    if midi_out:
        midi_out.send(mido.Message('note_on', note=note, velocity=127))

def trigger_pad_off(note):
    if note in active_pads:
        active_pads.remove(note)
    if midi_out:
        midi_out.send(mido.Message('note_off', note=note, velocity=0))

def handle_mouse_click(pos):
    for note, rect in pad_positions.items():
        if rect.collidepoint(pos):
            trigger_pad_on(note)
            draw_pads()
            time.sleep(0.1) 
            trigger_pad_off(note)

# main loop
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

        # get midi-events 
        for msg in midi_in.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                trigger_pad_on(msg.note)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                trigger_pad_off(msg.note)
                
            elif msg.type == 'control_change':
                cc_number = msg.control
                cc_value = msg.value
                
                if cc_number in cc_to_note_mapping:
                    target_note = cc_to_note_mapping[cc_number]
                    pad_volumes[target_note] = cc_value
                    
                    if target_note in sounds:
                        sounds[target_note].set_volume(cc_value / 127.0)

        draw_pads()
        clock.tick(30)

except KeyboardInterrupt:
    print("end programm ...")

finally:
    midi_in.close()
    if midi_out:
        midi_out.close()
    pygame.quit()
