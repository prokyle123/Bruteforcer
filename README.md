![Screenshot 2024-10-07 210129](https://github.com/user-attachments/assets/c2b187eb-60da-43ac-b3c9-a4133acf39b1)
The BruteForcer Plugin is a powerful tool designed for penetration testers, security researchers, and Wi-Fi enthusiasts who want to automate WPA/WPA2 handshake cracking using aircrack-ng. This plugin seamlessly integrates with Pwnagotchi, allowing users to monitor and brute force captured handshakes in real-time, while offering detailed feedback and intuitive UI integration to optimize the process.

🔑 Key Features
1. Real-Time Brute Force Progress
The BruteForcer Plugin provides real-time progress updates directly from aircrack-ng. You’ll see detailed status updates that include the current progress percentage and the words per second (WPS) performance during brute force attacks.
The Progress field (PR) dynamically updates throughout the attack, ensuring you can monitor how far along the brute force process is, providing greater visibility into long-running wordlist attacks.
2. Intuitive and Compact UI Integration
The plugin adds small, neatly formatted status messages to the bottom of your Pwnagotchi’s screen. These messages display the current SSID (abbreviated for space), the wordlist being used, and the current WPS (Words per Second).
The UI has been designed to make optimal use of limited screen space, providing you with the most essential information without overwhelming the display.
You’ll know at a glance which network is being attacked, which wordlist is in use, and how fast the brute force attack is progressing.
3. Single-Instance Brute Forcing
To prevent resource conflicts and ensure maximum stability, BruteForcer only runs one brute force attack at a time. This ensures that each handshake is attacked individually and prevents multiple attacks from overlapping.
This approach guarantees that your Pwnagotchi operates efficiently, focusing its resources on one task at a time, making it easier to track individual progress and results.
4. Automatic Retry on Failures
The plugin has built-in error handling and automatic retries. If a brute force attack times out or fails (e.g., due to an incomplete handshake), the plugin will automatically retry the attack up to three times.
This feature is particularly useful when dealing with challenging or incomplete handshakes, ensuring the highest possible success rate without manual intervention.
5. Detailed Logging and Debugging
BruteForcer logs every step of the brute force process, from the initial command to the final result, making it easy to review what’s happening under the hood.
The plugin logs real-time progress, detailed errors, and results from each attack, including whether a password was cracked or the attack failed. This allows for easier troubleshooting and fine-tuning of your approach to specific networks.
6. Flexible Wordlist Management
BruteForcer supports multiple wordlists, giving users the flexibility to use their favorite wordlists or cycle through multiple lists during brute force attacks.
Wordlists can be placed in a designated folder, and the plugin will automatically iterate through them during each attack, maximizing the chances of cracking the handshake.
You can easily update or swap out wordlists without changing the core configuration.
7. Optimized Handshake File Handling
The plugin efficiently monitors your handshake directory, ensuring that each .pcap file is processed and that no handshake is missed.
It tracks which handshakes have been processed, making sure that files are not brute forced multiple times unnecessarily, while providing clear feedback on how many files have been processed versus how many remain.
8. WPA/WPA2 Handshake Support
The BruteForcer Plugin is tailored for WPA/WPA2 security, focusing on capturing and cracking standard WPA handshakes. It supports .pcap files that contain the necessary EAPOL data for cracking WPA/WPA2 networks.
💡 How It Works
Monitor Directory for Handshake Files:

BruteForcer continuously monitors a designated directory for any new .pcap files (handshake captures). Once a new file is detected, the plugin automatically starts processing the file using the provided wordlists.
Initiate Brute Force Attack:

The plugin runs aircrack-ng in the background to brute force the WPA/WPA2 handshakes using the selected wordlist(s). You can configure the wordlist folder to contain multiple wordlists, which the plugin will iterate over.
Real-Time Progress Updates:

The plugin displays real-time updates of the brute force attack directly on the Pwnagotchi screen, showing the SSID being attacked, the wordlist in use, the progress percentage, and the WPS. These updates help you stay informed of the current attack’s progress without needing to check logs manually.
Log Results and Errors:

Once a brute force attack completes (either successfully or unsuccessfully), the results are logged and displayed. The plugin will show whether the password was cracked, or if the attack failed, along with any relevant error messages.
Handle Incomplete Handshakes:

If a handshake file does not contain EAPOL frames or is otherwise incomplete, the plugin skips the file and logs an error, ensuring that processing continues smoothly without manual intervention.
📋 Requirements
Pwnagotchi Device: This plugin is designed to run on Pwnagotchi devices with a display (e.g., e-paper, OLED) for real-time status updates.
Aircrack-ng: aircrack-ng must be installed and properly configured on the device for the plugin to function. The plugin runs aircrack-ng in the background for each brute force attack.
Captured Handshake Files: The plugin requires WPA/WPA2 handshake .pcap files to perform brute force attacks. These files can be captured using tools like airodump-ng, bettercap, or others.
Wordlists: A wordlist or multiple wordlists for brute forcing. Place these in the configured wordlist directory, and the plugin will use them during attacks.
🔧 Installation and Setup
Install the Plugin:

Copy the plugin files to your Pwnagotchi device in the appropriate plugin directory (/usr/local/share/pwnagotchi/custom-plugins/).
Configure the Plugin:

Define the directories for your handshake files and wordlists in the plugin configuration. You can also configure the delay between brute force attempts and set your retry limits.
Start the Plugin:

Once installed, the plugin will automatically start monitoring for handshake files and will initiate brute force attacks as soon as a new file is detected.
🎯 Who is This For?
The BruteForcer Plugin is perfect for security professionals, Wi-Fi enthusiasts, and anyone looking to automate WPA/WPA2 handshake cracking. Whether you’re conducting penetration tests, performing security audits, or just experimenting with Pwnagotchi, this plugin allows you to easily monitor and crack handshakes in a streamlined, efficient way.

📈 Future Enhancements
WPA3 Support: Future updates may include support for WPA3 handshakes as tools evolve to handle newer security protocols.
Graphical Progress: Additional visual enhancements to show graphical representations of brute force progress.
Advanced Error Handling: More granular error handling and recovery options for edge cases and complex handshake files.
