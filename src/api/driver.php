<?php
/*
 * cmv-php
 * github.com/01mu
 */

include_once 'cmv.php';

$host = '';
$user = '';
$pass = '';
$db = '';

$cmv = new cmv();

$cmv->conn($host, $user, $pass, $db);
