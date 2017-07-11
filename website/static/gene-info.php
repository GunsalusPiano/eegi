<?php

$table = 'Gene';

$primaryKey = 'id';

$columns = array(
  array('db' => 'id', 'dt' => 0 ),
  array('db' => 'cosmid_id', 'dt' => 1 ),
  array('db' => 'locus', 'dt' => 2 ),
  array('db' => 'gene_type', 'dt' => 3 ),
  array('db' => 'gene_class_description', 'dt' => 4 ),
  array('db' => 'functional_description', 'dt' => 5 )
);

$sql_details = array(
  'user' => 'alan',
  'db' => 'eegi',
  'host' => '127.0.0.1'
);

require( 'ssp.class.php' );

echo json_encode(
    SSP::simple( $_GET, $sql_details, $table, $primaryKey, $columns )
);
