<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo( 'charset' ); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">

    <!-- ─── Site Header ──────────────────────────────────────────────────── -->
    <header id="masthead" class="site-header" role="banner">
        <div class="header-inner container">

            <div class="header-identity">
                <p class="header-flag">Independent Civic Journalism</p>
                <?php if ( has_custom_logo() ) : ?>
                    <div class="site-logo"><?php the_custom_logo(); ?></div>
                <?php else : ?>
                    <a class="site-name" href="<?php echo esc_url( home_url( '/' ) ); ?>">
                        <?php echo esc_html( civic_publication_name() ); ?>
                    </a>
                <?php endif; ?>
                <p class="header-dateline">
                    <?php
                    echo esc_html( civic_city_name() ) . ', Texas &mdash; ';
                    echo esc_html( date_i18n( 'l, F j, Y' ) );
                    ?>
                </p>
            </div>

            <nav id="site-navigation" class="main-navigation" role="navigation" aria-label="<?php esc_attr_e( 'Primary', 'civic-record' ); ?>">
                <button class="menu-toggle" aria-controls="primary-menu" aria-expanded="false">
                    <span class="menu-toggle__bar"></span>
                    <span class="menu-toggle__bar"></span>
                    <span class="menu-toggle__bar"></span>
                    <span class="screen-reader-text"><?php esc_html_e( 'Menu', 'civic-record' ); ?></span>
                </button>
                <?php
                wp_nav_menu( [
                    'theme_location' => 'primary',
                    'menu_id'        => 'primary-menu',
                    'container'      => false,
                    'fallback_cb'    => 'civic_fallback_menu',
                ] );
                ?>
            </nav>

        </div><!-- .header-inner -->
    </header><!-- #masthead -->

    <div id="content" class="site-content">
<?php

/**
 * Fallback menu when no menu is assigned — lists top-level categories.
 */
function civic_fallback_menu(): void {
    $cats = get_categories( [ 'hide_empty' => true, 'number' => 8 ] );
    if ( ! $cats ) {
        return;
    }
    echo '<ul id="primary-menu">';
    echo '<li><a href="' . esc_url( home_url( '/' ) ) . '">Home</a></li>';
    foreach ( $cats as $cat ) {
        if ( $cat->slug === 'uncategorized' ) {
            continue;
        }
        printf(
            '<li><a href="%s">%s</a></li>',
            esc_url( get_category_link( $cat ) ),
            esc_html( $cat->name )
        );
    }
    echo '</ul>';
}
