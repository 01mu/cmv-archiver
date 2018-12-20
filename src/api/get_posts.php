<?php
/*
 * cmv-php
 * github.com/01mu
 */

include_once 'driver.php';

$limit = $_GET['limit'];
$order = $_GET['order'];
$start = $_GET['start'];
$sort = $_GET['sort'];

$cmv->get_posts($limit, $order, $start, $sort);
