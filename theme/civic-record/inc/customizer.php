<?php
/**
 * Civic Record — Customizer settings
 * City name, publication name, accent color, about text.
 */

defined( 'ABSPATH' ) || exit;

add_action( 'customize_register', function ( WP_Customize_Manager $wp_customize ) {

    // ─── Panel: Civic Record Identity ─────────────────────────────────────────
    $wp_customize->add_panel( 'civic_identity', [
        'title'    => __( 'Civic Record Identity', 'civic-record' ),
        'priority' => 30,
    ] );

    // ─── Section: Publication Info ─────────────────────────────────────────────
    $wp_customize->add_section( 'civic_publication', [
        'title'    => __( 'Publication Info', 'civic-record' ),
        'panel'    => 'civic_identity',
        'priority' => 10,
    ] );

    // City Name
    $wp_customize->add_setting( 'civic_city_name', [
        'default'           => 'City',
        'sanitize_callback' => 'sanitize_text_field',
        'transport'         => 'postMessage',
    ] );
    $wp_customize->add_control( 'civic_city_name', [
        'label'       => __( 'City Name', 'civic-record' ),
        'description' => __( 'Used in "Today in [City]" section header.', 'civic-record' ),
        'section'     => 'civic_publication',
        'type'        => 'text',
    ] );

    // Publication Name
    $wp_customize->add_setting( 'civic_publication_name', [
        'default'           => 'The City Record',
        'sanitize_callback' => 'sanitize_text_field',
        'transport'         => 'postMessage',
    ] );
    $wp_customize->add_control( 'civic_publication_name', [
        'label'   => __( 'Publication Name', 'civic-record' ),
        'section' => 'civic_publication',
        'type'    => 'text',
    ] );

    // About Text
    $wp_customize->add_setting( 'civic_about_text', [
        'default'           => 'An automated civic intelligence publication covering local government, development, and community news.',
        'sanitize_callback' => 'wp_kses_post',
        'transport'         => 'refresh',
    ] );
    $wp_customize->add_control( 'civic_about_text', [
        'label'   => __( 'About Text (sidebar)', 'civic-record' ),
        'section' => 'civic_publication',
        'type'    => 'textarea',
    ] );

    // ─── Section: Colors ───────────────────────────────────────────────────────
    $wp_customize->add_section( 'civic_colors', [
        'title'    => __( 'Accent Color', 'civic-record' ),
        'panel'    => 'civic_identity',
        'priority' => 20,
    ] );

    $wp_customize->add_setting( 'civic_accent_color', [
        'default'           => '#1A5C38',
        'sanitize_callback' => 'sanitize_hex_color',
        'transport'         => 'postMessage',
    ] );
    $wp_customize->add_control(
        new WP_Customize_Color_Control( $wp_customize, 'civic_accent_color', [
            'label'       => __( 'Accent Color', 'civic-record' ),
            'description' => __( 'Used for nav bar, category badges, and link highlights.', 'civic-record' ),
            'section'     => 'civic_colors',
        ] )
    );
} );

// Live preview JS for postMessage transports
add_action( 'customize_preview_init', function () {
    wp_enqueue_script(
        'civic-customizer-preview',
        CIVIC_URI . '/assets/js/customizer-preview.js',
        [ 'customize-preview' ],
        CIVIC_VERSION,
        true
    );
} );
