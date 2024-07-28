# BruteForce WPA Handshake Plugin for Pwnagotchi

## Overview

The BruteForce WPA Handshake Plugin is designed to enhance your Pwnagotchi by automating the process of brute-forcing WPA handshakes. It uses a specified wordlist to attempt to crack the WPA keys of captured handshakes and provides real-time feedback through the Pwnagotchi UI.

## Features

- **Automated Handshake Detection**: The plugin monitors a specified directory for WPA handshake files. When a new handshake file is detected, it automatically initiates a brute-force attack.
- **Real-Time UI Integration**: The plugin updates the Pwnagotchi UI with the status of the brute-force attack, including the SSID of the target network, the progress percentage, and the result of the attack (Cracked or Failed).
- **Single Task Execution**: To optimize performance and avoid conflicts, the plugin ensures that only one brute-force task runs at any given time.

## Detailed Description

### Automated Handshake Detection

Upon loading, the plugin scans a designated directory for existing WPA handshake files and processes them. It continues to monitor this directory in real-time, ensuring that any new handshakes are promptly subjected to a brute-force attack. This automation frees the user from manually initiating brute-force attacks on newly captured handshakes.

### Brute-Force Attacks

The core functionality of the plugin is its ability to perform brute-force attacks on WPA handshake files using a wordlist. The plugin leverages `aircrack-ng`, a powerful tool for network key cracking, to execute these attacks. By specifying a wordlist, the plugin systematically attempts each word as a possible WPA key, striving to uncover the correct key for the network.

### Real-Time UI Integration

The plugin enhances the Pwnagotchi user experience by providing real-time feedback on the brute-force process:

- **BF (Brute-Force Target)**: Displays the SSID (network name) or a portion of the SSID of the network currently being attacked.
- **PR (Progress)**: Shows the progress of the brute-force attack as a percentage, indicating how much of the wordlist has been attempted.
- **RE (Result)**: Indicates the outcome of the brute-force attack. It shows "Cracked" if the WPA key was successfully found and "Failed" if the attack did not succeed.

### Single Task Execution

To maintain system stability and performance, the plugin ensures that only one brute-force attack runs at a time. If a new handshake is detected while an attack is already in progress, the new handshake will be queued and processed once the current task is completed. This approach prevents resource conflicts and ensures that each attack receives the necessary system resources to execute efficiently.

## Use Cases

- **Network Security Auditing**: Network administrators can use the plugin to test the strength of WPA keys within their own networks, identifying weak passwords that could be easily compromised.
- **Educational Purposes**: Security professionals and enthusiasts can use the plugin to learn about WPA security and the brute-force attack process in a controlled environment.
- **Automation and Efficiency**: By automating the brute-force process and providing real-time updates, the plugin saves users time and effort, allowing them to focus on other tasks while the plugin handles handshake cracking.

## Conclusion

The BruteForce WPA Handshake Plugin is a powerful tool for automating WPA handshake brute-force attacks. With its automated detection, real-time UI integration, and efficient task management, it enhances the capabilities of Pwnagotchi and provides valuable insights into network security. Whether used for network auditing, education, or automation, this plugin is a valuable addition to any Pwnagotchi setup.
