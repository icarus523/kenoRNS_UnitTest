#!/bin/bash

# Directory containing the PEM files
DIRECTORY="."

# Change to the specified directory
cd "$DIRECTORY" || { echo "Directory not found"; exit 1; }

# Loop through all .pem files in the directory
for file in *.pem; do
    if [ -f "$file" ]; then
        # Generate SHA-256 fingerprint
        fingerprint=$(openssl x509 -in "$file" -noout -fingerprint -sha256)
        echo "$file\t$fingerprint"
    else
        echo "No PEM files found in the directory."
    fi
done
