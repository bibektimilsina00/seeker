<?php
header('Content-Type: text/html');
{
  $ok_status = $_POST['Status'];
  $lat = $_POST['Lat'];
  $lon = $_POST['Lon'];
  $acc = $_POST['Acc'];
  $alt = $_POST['Alt'];
  $dir = $_POST['Dir'];
  $spd = $_POST['Spd'];
  $dev_id = isset($_POST['DevId']) ? trim($_POST['DevId']) : '';

  $data = array(
    'status' => $ok_status,
    'lat' => $lat,
    'lon' => $lon,
    'acc' => $acc,
    'alt' => $alt,
    'dir' => $dir,
    'spd' => $spd,
    'dev_id' => $dev_id);

  $json_data = json_encode($data);

  $f = fopen('../../logs/result.txt', 'w+');
  fwrite($f, $json_data);
  fclose($f);
}
?>
