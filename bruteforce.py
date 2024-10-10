import os
import json
import time
import logging
import threading
import subprocess
import re
from typing import Set, Optional
from flask import Flask, render_template

import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK


class BruteForce(plugins.Plugin):
    __author__ = 'SKY'
    __version__ = '2.0.0'
    __license__ = 'GPL3'
    __description__ = 'A plugin to brute force WPA handshakes using aircrack-ng.'

    def __init__(self):
        # Initialize attributes that do not depend on configuration options
        self.status = "IDLE"
        self.progress = "0%"
        self.result = ""
        self.ui = None
        self.lock = threading.Lock()
        self.processed_files = 0
        self.total_files = 0
        self.cracked_count = 0
        self.current_task: Optional[subprocess.Popen] = None
        self.progress_file = "/root/bruteforce_progress.json"
        self.processed_files_set: Set[str] = set()
        self.stop_event = threading.Event()
        self.retry_limit = 3
        self.status_message = ""  # Holds the small status message for display

        # Tracking WPS, elapsed time, progress, and words processed
        self.wps_data = []  # Track words per second (WPS)
        self.elapsed_time_data = []  # Track elapsed time per handshake
        self.progress_data = []  # Track real-time progress percentage
        self.words_processed = 0  # Total words processed
        self.words_processed_abbr = ""  # Abbreviated words processed for display
        self.time_labels = []  # Track timestamps for WPS and Progress
        self.progress_time_labels = []  # Track time intervals for progress
        self.handshake_ssids = []  # Track handshake SSIDs for elapsed time

        # Set default values for handshake_dir, wordlist_folder, and delay_between_attempts
        self.handshake_dir = "/home/pi/handshakes"
        self.wordlist_folder = "/home/pi/wordlists"
        self.delay_between_attempts = 5  # Default delay between attempts in seconds

        # Flask setup for dashboard
        self.template_folder = '/usr/local/share/pwnagotchi/custom-plugins'
        self.app = Flask(__name__, template_folder=self.template_folder)
        self.dashboard_thread = threading.Thread(target=self.start_dashboard)
        self.dashboard_thread.daemon = True  # Ensure the thread exits when the plugin stops

    def on_configure(self, options):
        # Access configuration options
        self.options = options
        self.wordlist_folder = self.options.get("wordlist_folder", "/home/pi/wordlists")
        self.handshake_dir = self.options.get("handshake_dir", "/home/pi/handshakes")
        self.delay_between_attempts = self.options.get("delay_between_attempts", 5)  # Ensure it's set

    def on_loaded(self):
        logging.info("[bruteforce] Plugin loaded.")
        self.load_progress()

        # Start the Flask web server for the dashboard
        self.dashboard_thread.start()

        self.update_total_files()
        self.start_monitoring()

    def start_dashboard(self):
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html', 
                                   status=self.status,
                                   progress=self.progress,
                                   processed_files=self.processed_files,
                                   total_files=self.total_files,
                                   words_processed=self.words_processed,
                                   # Default to empty lists if variables are None or not available yet
                                   wps_data=self.words_per_second_data or [],
                                   time_data=self.time_data or [],
                                   elapsed_time_data=self.elapsed_time_data or [],
                                   handshake_data=self.handshake_data or [],
                                   progress_over_time_data=self.progress_over_time_data or [],
                                   cracked_count=self.cracked_count or 0,
                                   failed_count=self.failed_count or 0)

        # Start the Flask web server
        self.app.run(host='0.0.0.0', port=5000)

    def on_unloaded(self):
        logging.info("[bruteforce] Plugin unloaded.")
        self.stop_event.set()

    def on_ui_setup(self, ui):
        self.ui = ui
        ui_elements = {
            "bruteforce_status": ("BF:", self.status, (128, 60)),
            "bruteforce_progress": ("PR:", self.progress, (188, 60)),
            "bruteforce_result": ("RE:", self.result, (128, 68)),
            "bruteforce_total": ("TO:", f"{min(self.processed_files, self.total_files)}/{self.total_files}", (188, 68)),
            "bruteforce_cracked": ("CR:", f"{self.cracked_count}/{self.processed_files}", (133, 1)),
            # Status message at the bottom center with a smaller font size
            "bruteforce_step": ("", "Idle", (1, 13))  # Position this in the bottom center
        }
        for key, (label, value, position) in ui_elements.items():
            ui.add_element(
                key,
                LabeledValue(
                    color=BLACK,
                    label=label,
                    value=value,
                    position=position,
                    label_font=fonts.Bold,  # Bold for labels
                    text_font=fonts.Small,  # Use smaller font for the step status
                ),
            )

    def on_ui_update(self, ui):
        if self.ui:
            with ui._lock:
                ui.set("bruteforce_status", self.status)
                ui.set("bruteforce_progress", self.progress)
                ui.set("bruteforce_result", self.result)
                ui.set("bruteforce_total", f"{min(self.processed_files, self.total_files)}/{self.total_files}")
                ui.set("bruteforce_cracked", f"{self.cracked_count}/{self.processed_files}")
                ui.set("bruteforce_step", self.status_message)  # Small status message

    def start_monitoring(self):
        logging.info("[bruteforce] Starting handshake monitoring thread.")
        threading.Thread(target=self.monitor_handshakes, daemon=True).start()

    def monitor_handshakes(self):
        while not self.stop_event.is_set():
            new_files = self.get_new_handshakes()
            for pcap_file in new_files:
                self.run_bruteforce(pcap_file)
                time.sleep(self.delay_between_attempts)
            time.sleep(10)

    def get_new_handshakes(self) -> Set[str]:
        """
        Retrieves a set of new handshake files that have not been processed yet.

        Returns:
            Set[str]: A set containing the file paths of new .pcap files.
        """
        all_pcap_files = {
            os.path.join(root, file)
            for root, _, files in os.walk(self.handshake_dir)
            for file in files if file.endswith(".pcap")
        }
        new_files = all_pcap_files - self.processed_files_set
        return new_files

    def run_bruteforce(self, pcap_file, retries=0):
        with self.lock:
            # Ensure only one instance of the brute forcer runs
            if self.current_task is not None:
                return  # Exit if a task is already running

            # Start brute-forcing the current pcap file
            self.processed_files_set.add(pcap_file)

            # Extract SSID and wordlist, validate filename format
            if "_" in os.path.basename(pcap_file):
                ssid = os.path.basename(pcap_file).split("_")[0]  # Extract SSID
                wordlist = os.path.basename(pcap_file).split("_")[1][:4]  # Abbreviate wordlist for status
                logging.info(f"[bruteforce] Using SSID: {ssid} and wordlist abbreviation: {wordlist}")
            else:
                logging.error(f"[bruteforce] Invalid filename format for {pcap_file}")
                return  # Exit if filename format is invalid

            self.update_step_status(f"BF: Start {ssid}")
            
            # Get all wordlists in the specified folder
            wordlist_files = [
                os.path.join(self.wordlist_folder, f) for f in os.listdir(self.wordlist_folder)
                if os.path.isfile(os.path.join(self.wordlist_folder, f))
            ]

            start_time = time.time()  # Start timer for this handshake
            cracked_keys_file = "/root/cracked_keys.txt"  # Path to store cracked keys

            for wordlist in wordlist_files:
                # Update the status with the current wordlist and abbreviated SSID: "WL: <wordlist> <SSID>"
                self.update_step_status(f"WL: {os.path.basename(wordlist)} {ssid}")

                # Build the aircrack-ng command
                command = [
                    "aircrack-ng",
                    "-w", wordlist,
                    "-e", ssid,
                    pcap_file
                ]

                logging.info(f"[bruteforce] Running command: {' '.join(command)} with wordlist {wordlist} for network {ssid}")
                self.update_status("BRUTE", "0%", "")
                self.on_ui_update(self.ui)

                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    self.current_task = process

                    # Real-time progress updates and words per second
                    for line in iter(process.stdout.readline, ''):
                        logging.info(f"[bruteforce] aircrack-ng output: {line.strip()}")
                        # Update progress percentage more frequently
                        progress_match = re.search(r"(\d+\.\d+)%", line)
                        if progress_match:
                            progress = progress_match.group(1)
                            self.progress = str(int(float(progress))) + "%"
                            self.on_ui_update(self.ui)
                            self.progress_data.append(int(float(progress)))  # Track progress for graph
                        elif "KEY FOUND!" in line:
                            self.result = "Cracked"
                            self.cracked_count += 1
                            key_match = re.search(r"KEY FOUND! \[ (.+) \]", line)
                            if key_match:
                                cracked_key = key_match.group(1)
                                # Save the cracked key and SSID to a file
                                with open(cracked_keys_file, 'a') as f:
                                    f.write(f"SSID: {ssid}, Key: {cracked_key}\n")
                                logging.info(f"[bruteforce] Network {ssid} cracked! Key: {cracked_key}")
                            break
                        elif "words per second" in line:
                            wps_match = re.search(r"(\d+)\swords per second", line)
                            if wps_match:
                                wps = wps_match.group(1)
                                self.words_processed += int(wps)  # Accumulate total words processed
                                self.words_processed_abbr = self.abbreviate_number(self.words_processed)  # Abbreviate words processed
                                self.status_message = f"{ssid[:4]} {wordlist[:4]} {wps}W/s"
                                self.on_ui_update(self.ui)
                                self.wps_data.append(int(wps))  # Track WPS data for graph

                    stdout, stderr = process.communicate(timeout=600)

                    if stderr:
                        logging.error(f"[bruteforce] aircrack-ng error:\n{stderr}")

                    if process.returncode == 0 and "KEY FOUND!" in stdout:
                        self.result = "Cracked"
                        self.cracked_count += 1
                        logging.info(f"[bruteforce] Network {ssid} cracked!")
                    else:
                        self.result = "Failed"
                        logging.info(f"[bruteforce] Brute force attack failed for {ssid}.")

                except subprocess.TimeoutExpired:
                    logging.error(f"[bruteforce] aircrack-ng command timed out for wordlist {wordlist} and network {ssid}.")
                    process.kill()
                    self.result = "Timeout"
                    if retries < self.retry_limit:
                        self.update_step_status(f"BF: Retry {ssid}")
                        self.run_bruteforce(pcap_file, retries + 1)
                    else:
                        self.update_step_status(f"BF: Fail {ssid}")
                        logging.error(f"[bruteforce] Maximum retries reached for wordlist {wordlist} and network {ssid}.")
                except Exception as e:
                    logging.exception(f"[bruteforce] An unexpected error occurred with wordlist {wordlist} and network {ssid}: {e}")
                finally:
                    self.current_task = None
                    elapsed_time = time.time() - start_time  # Calculate elapsed time
                    self.elapsed_time_data.append(elapsed_time)  # Track elapsed time for graph

                    # Increment processed files after the command runs, whether successful or not
                    self.processed_files += 1
                    self.update_status("DONE", "100%", self.result)
                    self.save_progress()
                    self.update_step_status(f"BF: Wait {ssid}")
                    time.sleep(60)
                    self.on_ui_update(self.ui)
                    self.update_total_files()

    def update_step_status(self, message):
        """
        Updates the abbreviated step status message on the UI, including the SSID.
        """
        self.status_message = message
        if self.ui:
            with self.ui._lock:
                self.ui.set("bruteforce_step", message)
            self.on_ui_update(self.ui)

    def update_status(self, status, progress, result):
        """
        Updates the status variables.

        Args:
            status (str): The current status.
            progress (str): The current progress percentage.
            result (str): The result of the last operation.
        """
        self.status = status
        self.progress = progress
        self.result = result

    def update_total_files(self):
        """
        Updates the total number of handshake files.
        """
        self.total_files = sum(
            len([f for f in files if f.endswith('.pcap')])
            for _, _, files in os.walk(self.handshake_dir)
        )
        logging.info(f"[bruteforce] Total handshake files: {self.total_files}")

    def abbreviate_number(self, number):
        """
        Abbreviates a large number into a human-readable format with suffixes like K, M, B.
        """
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.2f}K"
        return str(number)

    def save_progress(self):
        """
        Saves the current progress to a JSON file.
        """
        progress_data = {
            'processed_files': self.processed_files,
            'cracked_count': self.cracked_count,
            'processed_files_list': list(self.processed_files_set),
            'words_processed': self.words_processed
        }
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f)
            logging.info("[bruteforce] Progress saved.")
        except Exception as e:
            logging.error(f"[bruteforce] Failed to save progress: {e}")

    def load_progress(self):
        """
        Loads progress from a JSON file if it exists.
        """
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress_data = json.load(f)
                    self.processed_files = progress_data.get('processed_files', 0)
                    self.cracked_count = progress_data.get('cracked_count', 0)
                    self.processed_files_set = set(progress_data.get('processed_files_list', []))
                    self.words_processed = progress_data.get('words_processed', 0)
                    self.words_processed_abbr = self.abbreviate_number(self.words_processed)
                logging.info("[bruteforce] Progress loaded.")
            except Exception as e:
                logging.error(f"[bruteforce] Failed to load progress: {e}")
        else:
            logging.info("[bruteforce] No saved progress found.")

    def reset_progress(self):
        """
        Deletes the saved progress by removing the progress file.
        """
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                logging.info("[bruteforce] Progress reset. Progress file deleted.")
                self.processed_files = 0
                self.cracked_count = 0
                self.words_processed = 0
                self.words_processed_abbr = ""
                self.processed_files_set.clear()
                self.on_ui_update(self.ui)  # Update the UI after reset
            else:
                logging.info("[bruteforce] No progress file found to delete.")
        except Exception as e:
            logging.error(f"[bruteforce] Failed to delete progress file: {e}")
