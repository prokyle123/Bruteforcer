BruteForce WPA Handshake Plugin for Pwnagotchi (v1.4.1)
Overview
The BruteForce WPA Handshake Plugin automates brute-forcing WPA handshakes on your Pwnagotchi. It monitors for handshake files, attempts to crack them using a wordlist, and provides real-time feedback via the Pwnagotchi UI.

What's New in v1.4.1
Persistent Cracking Progress: Now, the plugin saves cracked network and total file progress, allowing the session to continue even after a restart.
Announced Status: Added live status announcements at the top of the screen, indicating the current task (e.g., "Processing," "Idle," "Completed").
UI Enhancements: Redesigned interface to better show brute-forcing progress, results, and statistics.
Optimized Aircrack-ng Execution: Improved error handling and system resource management. The plugin efficiently manages large wordlists without crashing by delaying tasks and reducing system resource consumption.
Detailed Logs and Error Reporting: Better logging of errors such as "Resetting EAPOL Handshake decoder state" and improved reporting of brute-force results (Cracked/Failed).
Improved Handshake Management: Each detected handshake is processed in sequence, and results are saved, preventing multiple tasks from running simultaneously.
Features
Automated Handshake Detection: The plugin continuously monitors a specified directory for WPA handshake files and automatically starts the brute-force process when new handshakes are detected.
Aircrack-ng Integration: Uses aircrack-ng for brute-force attacks, attempting each word in the specified wordlist to crack WPA handshakes.
Real-Time UI Feedback: Provides live updates in the Pwnagotchi UI, showing the current task (BF: target network, PR: progress, RE: result).
System Resource Management: Delays between brute-force attempts help manage system resources efficiently, preventing memory exhaustion.
Detailed Description
Persistent Progress and Announcement Feature
The plugin tracks how many handshakes have been processed and how many have been successfully cracked. It saves the state across sessions, ensuring you never lose your progress after rebooting.

Additionally, the plugin uses a single-word status announcement at the top of the screen, indicating what it's doing next: "Idle," "Processing," or "Completed."

Aircrack-ng Execution
The core feature of the plugin is brute-forcing WPA handshakes using aircrack-ng. It takes a handshake file, runs aircrack-ng against it using a user-specified wordlist, and checks whether the password can be cracked.

Key highlights:

SSID Limitation: Only the first four characters of the SSID are shown for compact display.
Customizable Wordlist: Users can set their own wordlist in the configuration file.
Error Handling: If the handshake file has issues or aircrack-ng runs into problems, the errors are logged for easier debugging.
Real-Time UI Feedback
The plugin integrates seamlessly with Pwnagotchi’s UI:

BF (Brute-Force Target): Shows the SSID (or a portion) of the network being attacked.
PR (Progress): Displays the percentage progress of the brute-force attack.
RE (Result): Indicates the outcome—either "Cracked" or "Failed."
TO (Total): Shows the total number of processed files out of the entire handshake folder.
System Resource Management
To avoid crashing or overloading the system, the plugin manages memory efficiently:

Delay Between Attempts: Introduced delays between brute-force attempts to reduce system strain.
Error Recovery: If a handshake fails to process, the plugin will log the error and move to the next task.
Installation
Clone the Repository:

bash
Copy code

cd /usr/local/share/pwnagotchi/custom-plugins
git clone https://github.com/prokyle123/Bruteforcer.git
Configure the Plugin: Open the Pwnagotchi configuration file:

bash
Copy code

sudo nano /etc/pwnagotchi/config.toml
Add the Bruteforcer plugin under the [main.plugins] section:

toml
Copy code

[main.plugins.bruteforcer]
enabled = true
Adjust Plugin Settings: Optionally, configure your wordlist and handshake directory in /usr/local/share/pwnagotchi/custom-plugins/Bruteforcer.py:

python
Copy code

self.wordlist = "/home/pi/wordlists/top62.txt"
self.handshake_dir = "/home/pi/handshakes"
Restart Pwnagotchi:

bash
Copy code

sudo systemctl restart pwnagotchi

Usage
Once installed and enabled, the Bruteforcer plugin will automatically monitor your designated handshake directory and attempt to crack any new handshakes.
Results of each brute-force attempt are shown in the Pwnagotchi UI and logged.
You can view detailed logs in real-time by running:

bash
Copy code

sudo pwnagotchi --debug

Best Practices
Use Efficient Wordlists: Larger wordlists may cause memory issues on low-powered devices like Pwnagotchi. Test with smaller wordlists first and gradually increase size while monitoring resource usage.
Monitor Logs: Regularly check logs for errors or failed attempts, which can help you troubleshoot issues with handshakes or wordlist configurations.
