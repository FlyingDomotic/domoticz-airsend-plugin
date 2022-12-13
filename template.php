<?php
$domoticz = "##URL##";
$idx = "##IDX##";

$raw = file_get_contents('php://input');
$data = json_decode($raw, true, 512, JSON_BIGINT_AS_STRING);

if (is_array($data) && isset($data['events'])) {
	foreach ($data['events'] as $i => $val) {
		$collectdate = strftime("%Y-%m-%d %H:%M:%S", ($val['timestamp']/1000));
		$val["original_timestamp"] = $val['timestamp'];
		$val["localip"] = $data['localip'];
		$val["timestamp"] = $collectdate;
		$url = $domoticz."json.htm?type=command&param=udevice&idx=".$idx."&nvalue=0&svalue=".urlencode(json_encode($val));
		$ch = curl_init();
		curl_setopt($ch, CURLOPT_URL, $url);
		curl_setopt($ch, CURLOPT_HEADER, FALSE);
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
		$data = curl_exec($ch);
		if(!curl_errno($ch)){
		  echo $data;
		} else {
		  echo 'Curl error: ' . curl_error($tuCurl);
		}
		curl_close($ch);
	}
}
?>