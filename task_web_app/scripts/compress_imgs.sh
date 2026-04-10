#!/bin/bash

# Directory containing the images
INPUT_DIR="../stimuli/flowers/original_imgs/"
# Directory to save the resized images
OUTPUT_DIR="../stimuli/flowers/small_imgs/"
# Resize width (adjust as needed)
# RESIZE_WIDTH=85 # size for default imgs
RESIZE_WIDTH=55 # size for small images
# Resize height (adjust as needed, 0 to maintain aspect ratio)
RESIZE_HEIGHT=0

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Loop through each image in the input directory
for image in "$INPUT_DIR"/*; do
    if [ -f "$image" ]; then
        # Get the base name of the file (without path)
        base_name=$(basename "$image")
        # Define the output file path
        output_file="$OUTPUT_DIR/$base_name"
        # Resize the image
        magick "$image" -resize "${RESIZE_WIDTH}" "$output_file"
        echo "Resized $image and saved to $output_file"
    else
        echo "Skipping non-file $image"
    fi
done

echo "Image resizing complete."
