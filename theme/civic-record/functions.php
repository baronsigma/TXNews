<?php
/**
 * Civic Record — functions.php
 * Theme setup, enqueue, customizer, widgets, REST helpers.
 */

defined( 'ABSPATH' ) || exit;

define( 'CIVIC_VERSION', '1.0.0' );
define( 'CIVIC_DIR', get_template_directory() );
define( 'CIVIC_URI', get_template_directory_uri() );

// ─── Theme Setup ────────────────────────────────────────────────────────────

add_action( 'after_setup_theme', function () {
    add_theme_support( 'title-tag' );
    add_theme_support( 'post-thumbnails' );
    add_theme_support( 'html5', [ 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption' ] );
    add_theme_support( 'customize-selective-refresh-widgets' );
    add_theme_support( 'responsive-embeds' );

    register_nav_menus( [
        'primary' => __( 'Primary Navigation', 'civic-record' ),
        'footer'  => __( 'Footer Navigation', 'civic-record' ),
    ] );
} );

// ─── Enqueue ─────────────────────────────────────────────────────────────────

add_action( 'wp_enqueue_scripts', function () {
    wp_enqueue_style(
        'civic-record-main',
        CIVIC_URI . '/assets/css/main.css',
        [],
        CIVIC_VERSION
    );
    wp_enqueue_script(
        'civic-record-main',
        CIVIC_URI . '/assets/js/main.js',
        [],
        CIVIC_VERSION,
        true
    );

    // Inline accent color from customizer
    $accent = get_theme_mod( 'civic_accent_color', '#1A5C38' );
    $css    = ":root { --accent-color: " . sanitize_hex_color( $accent ) . "; }";
    wp_add_inline_style( 'civic-record-main', $css );
} );

// ─── Sidebar Registration ─────────────────────────────────────────────────────

add_action( 'widgets_init', function () {
    $defaults = [
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ];

    register_sidebar( array_merge( $defaults, [
        'name' => __( 'Primary Sidebar', 'civic-record' ),
        'id'   => 'sidebar-primary',
    ] ) );

    register_sidebar( array_merge( $defaults, [
        'name' => __( 'Footer Widgets', 'civic-record' ),
        'id'   => 'sidebar-footer',
    ] ) );
} );

// ─── Includes ────────────────────────────────────────────────────────────────

require_once CIVIC_DIR . '/inc/customizer.php';
require_once CIVIC_DIR . '/inc/widgets.php';

// ─── Helper Functions ─────────────────────────────────────────────────────────

/**
 * Return posts for a given category slug, with caching.
 *
 * @param string $slug      WP category slug.
 * @param int    $count     Number of posts to return.
 * @param int    $offset    Offset for pagination.
 * @return WP_Post[]
 */
function civic_get_category_posts( string $slug, int $count = 5, int $offset = 0 ): array {
    $cache_key = "civic_cat_{$slug}_{$count}_{$offset}";
    $posts = wp_cache_get( $cache_key, 'civic_record' );
    if ( false === $posts ) {
        $posts = get_posts( [
            'category_name'  => $slug,
            'numberposts'    => $count,
            'offset'         => $offset,
            'post_status'    => 'publish',
            'no_found_rows'  => true,
        ] );
        wp_cache_set( $cache_key, $posts, 'civic_record', 300 );
    }
    return $posts ?: [];
}

/**
 * Render a section header with optional "View All" link.
 *
 * @param string      $title    Section title.
 * @param string|null $cat_slug Category slug for "View All" link.
 */
function civic_section_header( string $title, ?string $cat_slug = null ): void {
    echo '<div class="section-header">';
    echo '<h2 class="section-title">' . esc_html( $title ) . '</h2>';
    if ( $cat_slug ) {
        $url = get_category_link( get_category_by_slug( $cat_slug ) );
        if ( $url ) {
            echo '<a href="' . esc_url( $url ) . '" class="section-more">View all &rarr;</a>';
        }
    }
    echo '</div>';
}

/**
 * Render an article card (used in Latest Updates, etc.)
 *
 * @param WP_Post $post   The post object.
 * @param string  $size   'small'|'medium'|'large'
 */
function civic_article_card( WP_Post $post, string $size = 'medium' ): void {
    $cats    = get_the_category( $post->ID );
    $cat     = $cats ? $cats[0] : null;
    $excerpt = wp_trim_words( get_the_excerpt( $post ), 20, '…' );
    $url     = get_permalink( $post );
    ?>
    <article class="article-card article-card--<?php echo esc_attr( $size ); ?>">
        <?php if ( has_post_thumbnail( $post ) ) : ?>
            <a href="<?php echo esc_url( $url ); ?>" class="card-thumb">
                <?php echo get_the_post_thumbnail( $post, 'medium', [ 'loading' => 'lazy' ] ); ?>
            </a>
        <?php endif; ?>
        <div class="card-body">
            <?php if ( $cat ) : ?>
                <a href="<?php echo esc_url( get_category_link( $cat ) ); ?>" class="cat-badge">
                    <?php echo esc_html( $cat->name ); ?>
                </a>
            <?php endif; ?>
            <h3 class="card-title">
                <a href="<?php echo esc_url( $url ); ?>"><?php echo esc_html( get_the_title( $post ) ); ?></a>
            </h3>
            <?php if ( $size !== 'small' ) : ?>
                <p class="card-excerpt"><?php echo esc_html( $excerpt ); ?></p>
            <?php endif; ?>
            <time class="card-date" datetime="<?php echo esc_attr( get_the_date( 'c', $post ) ); ?>">
                <?php echo esc_html( get_the_date( 'M j, Y', $post ) ); ?>
            </time>
        </div>
    </article>
    <?php
}

/**
 * Return the city name from theme customizer (used in templates).
 */
function civic_city_name(): string {
    return get_theme_mod( 'civic_city_name', get_bloginfo( 'name' ) );
}

/**
 * Return the publication name from theme customizer.
 */
function civic_publication_name(): string {
    return get_theme_mod( 'civic_publication_name', get_bloginfo( 'name' ) );
}

// ─── REST API: Stats endpoint ─────────────────────────────────────────────────
// Allows n8n to push stats values: permits issued, median price, population, homes for sale

add_action( 'rest_api_init', function () {
    register_rest_route( 'civic/v1', '/stats', [
        'methods'             => 'POST',
        'callback'            => 'civic_rest_update_stats',
        'permission_callback' => function ( WP_REST_Request $req ) {
            return current_user_can( 'edit_posts' );
        },
        'args' => [
            'permits_issued'    => [ 'type' => 'integer', 'sanitize_callback' => 'absint' ],
            'median_home_price' => [ 'type' => 'string',  'sanitize_callback' => 'sanitize_text_field' ],
            'population'        => [ 'type' => 'string',  'sanitize_callback' => 'sanitize_text_field' ],
            'homes_for_sale'    => [ 'type' => 'integer', 'sanitize_callback' => 'absint' ],
            'period_label'      => [ 'type' => 'string',  'sanitize_callback' => 'sanitize_text_field' ],
        ],
    ] );

    register_rest_route( 'civic/v1', '/stats', [
        'methods'             => 'GET',
        'callback'            => 'civic_rest_get_stats',
        'permission_callback' => '__return_true',
    ] );
} );

function civic_rest_update_stats( WP_REST_Request $request ): WP_REST_Response {
    $fields = [ 'permits_issued', 'median_home_price', 'population', 'homes_for_sale', 'period_label' ];
    foreach ( $fields as $field ) {
        $val = $request->get_param( $field );
        if ( null !== $val ) {
            update_option( "civic_stats_{$field}", $val );
        }
    }
    update_option( 'civic_stats_updated', current_time( 'mysql' ) );
    return new WP_REST_Response( [ 'success' => true ], 200 );
}

function civic_rest_get_stats( WP_REST_Request $request ): WP_REST_Response {
    return new WP_REST_Response( [
        'permits_issued'    => get_option( 'civic_stats_permits_issued', 0 ),
        'median_home_price' => get_option( 'civic_stats_median_home_price', '—' ),
        'population'        => get_option( 'civic_stats_population', '—' ),
        'homes_for_sale'    => get_option( 'civic_stats_homes_for_sale', 0 ),
        'period_label'      => get_option( 'civic_stats_period_label', 'This Week' ),
        'updated'           => get_option( 'civic_stats_updated', '' ),
    ], 200 );
}
