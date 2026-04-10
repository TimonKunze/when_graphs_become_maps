<?php
// ATTRIBUTION: Original script by 
// https://kywch.github.io/jsPsych-in-Qualtrics/save-php/ (accessed 2024-03-29)
// but modified by me to allow for continuous saving 
// of data, i.e. writing to a file that already exist.

// WARNING: the below config can cause a serious security issue.
// Please read https://portswigger.net/web-security/cors/access-control-allow-origin
// Once you are done testing, you should limit the access:

// header('Access-Control-Allow-Origin: https://brainsci.uber.space');
header('Access-Control-Allow-Origin: *');

// NOTE: the below code expects three fields and will NOT work if any of these is missing.
// - data_dir: specify the server directory to store data
// - file_name: specify the filename of the data being saved, which can include subject id
// - exp_data: contain the full json/csv data to be saved

if (isset($_POST['exp_data']) == false) { 
    echo('Hello'); 
    exit; 
}

// // Append in json-line (.jsonl) format
// $exp_data_bar = $_POST['exp_data'];
// $exp_data = $exp_data_bar . "\n";
$exp_data = $_POST['exp_data'];

// $input = file_get_contents('php://input');
// $exp_data = json_decode($exp_data, true);

/* prevent XSS:  */
$_POST = filter_input_array(INPUT_POST, FILTER_SANITIZE_STRING);

if (isset($_POST['data_dir']) == true)
{
    $data_dir = $_POST['data_dir']; // data directory
} else { exit; }

if (isset($_POST['file_name']) == true)
{
    $file_name = $_POST['file_name']; // mturk_id
} else { exit; }

// write the file to disk
// NOTE: you must make the data directory by all users
// For example, by running `chmod 772` to give a write access to EVERYONE
// file_put_contents($data_dir.'/'.$file_name, $exp_data);
file_put_contents($data_dir . '/' . $file_name, $exp_data, FILE_APPEND | LOCK_EX);

exit;
?>
