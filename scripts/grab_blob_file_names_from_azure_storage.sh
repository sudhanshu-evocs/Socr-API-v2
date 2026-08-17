#!/bin/bash

# Define your storage account details
container_name=""
account_name=""
sas_token=""
max_iterations=200

# Initialize marker and counter
marker=""
counter=0

# Function to list blobs and capture the next marker
list_blobs() {
    local marker_param=""
    if [ -n "$marker" ]; then
        marker_param="--marker $marker"
    fi

    az storage blob list -c $container_name --account-name $account_name --sas-token "$sas_token" $marker_param --output json > blobs.json 2> marker.txt

    # Extract blob names
    jq -r '.[].name' blobs.json >> all_blobs.txt

    # Extract the next marker from the error output
    marker=$(grep -oP '(?<=WARNING: ).*' marker.txt | awk 'NR==2')
}

# Loop to handle pagination
while [ $counter -lt $max_iterations ]; do
    list_blobs
    echo "Next marker: $marker"
    if [ -z "$marker" ]; then
        break
    fi
    counter=$((counter + 1))
done

# Clean up
rm blobs.json marker.txt
