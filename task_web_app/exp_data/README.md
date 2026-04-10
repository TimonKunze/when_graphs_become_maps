# Experiment Data Endpoint

This folder contains the server-side endpoint used by the web experiment to append participant data to disk.

## Files

- `save_data.php`: receives POSTed experiment data and appends it to a file.
- `index.html`: blocks directory listing when served.
- `.htaccess`: web-server rule for using `index.html` as the directory index.

## Minimal setup

1. Deploy this folder on a PHP-enabled web server.
2. Make sure the directory is writable by the web-server user.
3. Keep `index.html` and `.htaccess` in place so the directory contents are not listed publicly.
4. Point the frontend save call at `exp_data/save_data.php`.

The endpoint expects these POST fields:

- `data_dir`: target directory for saved files.
- `file_name`: output filename.
- `exp_data`: experiment payload to append.

## Security note

The current PHP script allows `Access-Control-Allow-Origin: *` for convenience during testing. Restrict this to your production domain before deployment.

Reference: https://kywch.github.io/jsPsych-in-Qualtrics/save-php/
