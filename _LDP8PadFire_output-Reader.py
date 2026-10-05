
import pygame.midi
import time

# Initialisiere Pygame MIDI
pygame.midi.init()

# ==================== DEVICE SELECTION ====================
# Optional: Set device manually (leave as None to prompt user)
SELECTED_DEVICE = None
# =========================================================

# List all available MIDI input devices
print("Available MIDI-devices:")
print("-" * 50)
device_count = pygame.midi.get_count()
available_devices = []

for i in range(device_count):
    device_info = pygame.midi.get_device_info(i)
    # device_info format: (interface, name, input, output, opened)
    if device_info[2]:  # Check if it's an input device
        device_name = device_info[1].decode('utf-8') if isinstance(device_info[1], bytes) else device_info[1]
        available_devices.append((i, device_name))
        print(f"Index {i}: {device_name}")

print("-" * 50)
print()

# Determine which device to use
if SELECTED_DEVICE is not None:
    device_id = SELECTED_DEVICE
    print(f"Using device with index {device_id}")
else:
    # Prompt user to select a device
    if available_devices:
        while True:
            try:
                user_input = input(f"Choose a device (0-{device_count-1}), or press enter for default: ").strip()
                if user_input == "":
                    device_id = pygame.midi.get_default_input_id()
                    print(f"Using default device (Index {device_id})")
                    break
                device_id = int(user_input)
                if device_id in range(device_count):
                    device_info = pygame.midi.get_device_info(device_id)
                    if device_info[2]:  # Check if it's an input device
                        print(f"Device used: Index {device_id}")
                        break
                    else:
                        print(f"Device {device_id} is no inputdevice. Choose again")
                else:
                    print(f"Wrong. Please choose from 0 to {device_count-1}.")
            except ValueError:
                print("Please type a number.")
    else:
        print("No midi devices found")
        pygame.midi.quit()
        exit()

print()

# open midi device
input_device = pygame.midi.Input(device_id)

print("MIDI-Device opened. You can press pads...")

try:
    while True:
        if input_device.poll():
            midi_events = input_device.read(10)  # up to 10 
            for event in midi_events:
                midi_data = event[0]
                print(f"MIDI-Data: {midi_data}")

        time.sleep(0.01)

except KeyboardInterrupt:
    print("Proamm ended")

finally:
    input_device.close()
    pygame.midi.quit()
