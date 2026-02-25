<?php
/**
 * Civic Record — Custom Widgets
 *
 * 1. Civic_Stats_Widget    — "This Week in Numbers" sidebar block
 * 2. Civic_About_Widget    — Publication mission statement
 * 3. Civic_Meetings_Widget — Upcoming meetings list
 */

defined( 'ABSPATH' ) || exit;

add_action( 'widgets_init', function () {
    register_widget( 'Civic_Stats_Widget' );
    register_widget( 'Civic_About_Widget' );
    register_widget( 'Civic_Meetings_Widget' );
} );

// ─── Stats Widget ─────────────────────────────────────────────────────────────

class Civic_Stats_Widget extends WP_Widget {

    public function __construct() {
        parent::__construct(
            'civic_stats_widget',
            __( 'Civic: This Week in Numbers', 'civic-record' ),
            [ 'description' => __( 'Displays stats: permits, home price, population, homes for sale.', 'civic-record' ) ]
        );
    }

    public function widget( $args, $instance ) {
        $city         = civic_city_name();
        $label        = get_option( 'civic_stats_period_label', 'This Week' );
        $permits      = get_option( 'civic_stats_permits_issued', '—' );
        $median       = get_option( 'civic_stats_median_home_price', '—' );
        $population   = get_option( 'civic_stats_population', '—' );
        $homes        = get_option( 'civic_stats_homes_for_sale', '—' );
        $updated      = get_option( 'civic_stats_updated', '' );

        echo $args['before_widget'];
        ?>
        <div class="stats-widget">
            <div class="stats-widget__header">
                <span class="stats-widget__label"><?php echo esc_html( $label ); ?> in <?php echo esc_html( $city ); ?></span>
            </div>
            <ul class="stats-widget__list">
                <li class="stats-widget__item">
                    <span class="stats-widget__value"><?php echo esc_html( $permits ); ?></span>
                    <span class="stats-widget__key">Permits Issued</span>
                </li>
                <li class="stats-widget__item">
                    <span class="stats-widget__value"><?php echo esc_html( $median ); ?></span>
                    <span class="stats-widget__key">Median Home Price</span>
                </li>
                <li class="stats-widget__item">
                    <span class="stats-widget__value"><?php echo esc_html( $population ); ?></span>
                    <span class="stats-widget__key">Population</span>
                </li>
                <li class="stats-widget__item">
                    <span class="stats-widget__value"><?php echo esc_html( $homes ); ?></span>
                    <span class="stats-widget__key">Homes for Sale</span>
                </li>
            </ul>
            <?php if ( $updated ) : ?>
                <p class="stats-widget__updated">Updated <?php echo esc_html( human_time_diff( strtotime( $updated ) ) ); ?> ago</p>
            <?php endif; ?>
        </div>
        <?php
        echo $args['after_widget'];
    }

    public function form( $instance ) {
        echo '<p>' . esc_html__( 'Stats are pushed via the Civic REST API (/wp-json/civic/v1/stats). No configuration needed here.', 'civic-record' ) . '</p>';
    }

    public function update( $new_instance, $old_instance ) {
        return $old_instance;
    }
}

// ─── About Widget ─────────────────────────────────────────────────────────────

class Civic_About_Widget extends WP_Widget {

    public function __construct() {
        parent::__construct(
            'civic_about_widget',
            __( 'Civic: About Publication', 'civic-record' ),
            [ 'description' => __( 'Displays the publication mission statement.', 'civic-record' ) ]
        );
    }

    public function widget( $args, $instance ) {
        $pub   = civic_publication_name();
        $about = get_theme_mod( 'civic_about_text', 'An automated civic intelligence publication.' );

        echo $args['before_widget'];
        ?>
        <div class="about-widget">
            <p class="about-widget__name"><?php echo esc_html( $pub ); ?></p>
            <p class="about-widget__text"><?php echo wp_kses_post( $about ); ?></p>
        </div>
        <?php
        echo $args['after_widget'];
    }

    public function form( $instance ) {
        echo '<p>' . esc_html__( 'Text is pulled from Appearance → Customize → Civic Record Identity.', 'civic-record' ) . '</p>';
    }

    public function update( $new_instance, $old_instance ) {
        return $old_instance;
    }
}

// ─── Meetings Widget ─────────────────────────────────────────────────────────

class Civic_Meetings_Widget extends WP_Widget {

    public function __construct() {
        parent::__construct(
            'civic_meetings_widget',
            __( 'Civic: Upcoming Meetings', 'civic-record' ),
            [ 'description' => __( 'Shows latest civic governance posts as upcoming meetings.', 'civic-record' ) ]
        );
    }

    public function widget( $args, $instance ) {
        $posts = civic_get_category_posts( 'civic-governance', 3 );
        if ( ! $posts ) {
            return;
        }

        echo $args['before_widget'];
        echo $args['before_title'] . esc_html__( 'Upcoming Meetings', 'civic-record' ) . $args['after_title'];
        echo '<ul class="meetings-list">';
        foreach ( $posts as $post ) {
            $date = get_the_date( 'M j', $post );
            printf(
                '<li class="meetings-list__item"><span class="meetings-list__date">%s</span><a href="%s">%s</a></li>',
                esc_html( $date ),
                esc_url( get_permalink( $post ) ),
                esc_html( get_the_title( $post ) )
            );
        }
        echo '</ul>';
        echo $args['after_widget'];
    }

    public function form( $instance ) {
        echo '<p>' . esc_html__( 'Displays latest posts in the "civic-governance" category.', 'civic-record' ) . '</p>';
    }

    public function update( $new_instance, $old_instance ) {
        return $old_instance;
    }
}
