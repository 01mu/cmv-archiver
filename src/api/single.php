<?php
/*
 * cmv-php
 * github.com/01mu
 */

include_once 'driver.php';

$id = $_GET['id'];

$cmv->single($id);
