<?php
/*
 * cmv-php
 * github.com/01mu
 */

include_once 'driver.php';

$limit = $_GET['limit'];
$query = $_GET['search']
$start = $_GET['start'];

$cmv->search_posts($limit, $query, $start);
