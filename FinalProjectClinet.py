import socket
import json
import PySimpleGUI as sg
import threading
import platform

# Check if the platform is Windows
if platform.system().lower() == 'windows':
    sg.popup_error('Unsupported platform: Windows', title='Error')
    exit()

# Unicode symbols for ON and OFF
CIRCLE = '●'  # Unicode symbol 9899 for ON
CIRCLE_OUTLINE = '○'  # Unicode symbol 9898 for OFF

def update_gui(json_data, window_main, window_separate):  
    try:
        formatted_data = [
            f"Core Temperature: {json_data['Core Temperature']}",
            f"GPU Temperature: {json_data['GPU Temperature']}",
            f"CPU Temperature: {json_data['CPU Temperature']}",
            f"Voltage: {json_data['Voltage']}",
            f"GPU Core Speed: {json_data['GPU Core Speed']}",
           
           
            f"Iteration Count: {json_data['iteration_count']}",
        ]
        window_main['-DATA-'].update('\n'.join(formatted_data))
       
        # Update LED in the main window
        window_main['-LED-'].update(CIRCLE if json_data['LED_status'] else CIRCLE_OUTLINE, text_color='red')
       
        # Update Iteration Count and Blinking Light in the separate window
        window_separate['-ITERATION_COUNT-'].update(str(json_data['iteration_count']))
        window_separate['-LED-'].update(CIRCLE if json_data['LED_status'] else CIRCLE_OUTLINE, text_color='red')
    except KeyError as e:
        formatted_data = [f"Error: Key {e} not found in JSON data"]
        window_main['-DATA-'].update('\n'.join(formatted_data))

def receive_data(client, window_main, window_separate, exit_program):
    interval_counter = 0
    while interval_counter < 51 and not exit_program.is_set():
        try:
            chunk = client.recv(4096).decode('utf-8') 
            if not chunk:
                break

            json_data = json.loads(chunk)
            update_gui(json_data, window_main, window_separate)
            interval_counter += 1
        except Exception as e:
            print(f"Error receiving data: {e}") 
            break

# Set up the socket client
client = socket.socket()
host = '192.168.0.124'  # Use localhost or the actual IP of the Raspberry Pi
port = 5031

# Define the PySimpleGUI layout for the main window
layout_main = [
    [sg.Text("Received Data:", font=('Helvetica', 14))],
    [sg.Multiline("", key='-DATA-', size=(40, 10), font=('Helvetica', 12), background_color='lightblue')],
    [sg.Text("", key='-LED-', font=('Helvetica', 14), text_color='green')],
    [sg.Button('Exit')],
]

# Create the main PySimpleGUI window
window_main = sg.Window("Client GUI", layout_main, finalize=True)

# Define the PySimpleGUI layout for the separate GUI
layout_separate = [
    [sg.Text("Iteration Count:", font=('Helvetica', 14))],
    [sg.Text("0", key='-ITERATION_COUNT-', font=('Helvetica', 14))],
    [sg.Text("", key='-LED-', font=('Helvetica', 14), text_color='green')],
    [sg.Button('Exit')],
]

# Create the separate PySimpleGUI window
window_separate = sg.Window("Iteration Count and Blinking Light", layout_separate, finalize=True)

try:
    # Connect to the Raspberry Pi's socket server
    client.connect((host, port))

    # Event to signal the exit of the program
    exit_program = threading.Event()

    # Start a thread to receive data and update the GUI
    thread = threading.Thread(target=receive_data, args=(client, window_main, window_separate, exit_program), daemon=True)
    thread.start()

    # Event loop for the main PySimpleGUI window
    while True:
        event_main, values_main = window_main.read(timeout=100)
        if event_main == sg.WIN_CLOSED or exit_program.is_set() or event_main == 'Exit':
            break

        event_separate, values_separate = window_separate.read(timeout=100)
        if event_separate == sg.WIN_CLOSED or exit_program.is_set() or event_separate == 'Exit':
            break

except Exception as e:
    print(f"Error: {e}")

finally:
    # Set the exit event to signal the thread to stop
    exit_program.set()

    # Close the client socket
    client.close()

    # Close the PySimpleGUI windows
    window_main.close()
    window_separate.close()
