<?php
/**
 * sidebar.php — primary sidebar
 */

if ( ! is_active_sidebar( 'sidebar-primary' ) ) {
    return;
}
?>

<div class="sidebar-widgets">
    <?php dynamic_sidebar( 'sidebar-primary' ); ?>
</div>
