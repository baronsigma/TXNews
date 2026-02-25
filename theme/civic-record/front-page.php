<?php
/**
 * Civic Record — front-page.php
 * Homepage with all civic sections.
 * Category slugs: development, civic-governance, business, public-notices,
 *                 schools-education, new-coming-soon
 */

get_header();
$city = civic_city_name();
?>

<main id="main" class="site-main" role="main">

    <!-- ═══════════════════════════════════════════════════════════════════════
         TODAY IN [CITY] — hero section, 3 most recent posts
    ═══════════════════════════════════════════════════════════════════════════ -->
    <?php
    $hero_posts = get_posts( [
        'numberposts' => 3,
        'post_status' => 'publish',
        'no_found_rows' => true,
    ] );
    ?>
    <?php if ( $hero_posts ) : ?>
    <section class="section section--hero" aria-labelledby="today-heading">
        <div class="container">
            <?php civic_section_header( 'Today in ' . $city ); ?>
            <div class="hero-grid">
                <?php
                $first = true;
                foreach ( $hero_posts as $post ) :
                    setup_postdata( $post );
                    $cats    = get_the_category( $post->ID );
                    $cat     = $cats ? $cats[0] : null;
                    $url     = get_permalink( $post );
                    $excerpt = wp_trim_words( get_the_excerpt( $post ), $first ? 35 : 20, '…' );
                    ?>
                    <article class="hero-item hero-item--<?php echo $first ? 'lead' : 'secondary'; ?>">
                        <?php if ( has_post_thumbnail( $post ) ) : ?>
                            <a href="<?php echo esc_url( $url ); ?>" class="hero-item__thumb">
                                <?php echo get_the_post_thumbnail( $post, $first ? 'large' : 'medium', [ 'loading' => 'lazy' ] ); ?>
                            </a>
                        <?php endif; ?>
                        <div class="hero-item__body">
                            <?php if ( $cat ) : ?>
                                <a href="<?php echo esc_url( get_category_link( $cat ) ); ?>" class="cat-badge">
                                    <?php echo esc_html( $cat->name ); ?>
                                </a>
                            <?php endif; ?>
                            <h2 class="hero-item__title">
                                <a href="<?php echo esc_url( $url ); ?>"><?php the_title(); ?></a>
                            </h2>
                            <p class="hero-item__excerpt"><?php echo esc_html( $excerpt ); ?></p>
                            <time class="card-date" datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
                                <?php echo esc_html( get_the_date( 'M j, Y' ) ); ?>
                            </time>
                        </div>
                    </article>
                    <?php
                    $first = false;
                endforeach;
                wp_reset_postdata();
                ?>
            </div><!-- .hero-grid -->
        </div>
    </section>
    <?php endif; ?>

    <!-- ═══════════════════════════════════════════════════════════════════════
         LATEST UPDATES — 4-card grid of most recent posts (skip hero)
    ═══════════════════════════════════════════════════════════════════════════ -->
    <?php
    $latest_posts = get_posts( [
        'numberposts'  => 4,
        'offset'       => 3,
        'post_status'  => 'publish',
        'no_found_rows' => true,
    ] );
    ?>
    <?php if ( $latest_posts ) : ?>
    <section class="section section--latest" aria-labelledby="latest-heading">
        <div class="container">
            <?php civic_section_header( 'Latest Updates' ); ?>
            <div class="card-grid card-grid--4">
                <?php foreach ( $latest_posts as $post ) : ?>
                    <?php civic_article_card( $post, 'small' ); ?>
                <?php endforeach; ?>
            </div>
        </div>
    </section>
    <?php endif; ?>

    <!-- ═══════════════════════════════════════════════════════════════════════
         TWO-COLUMN BAND: Development Tracker + Civic Governance
    ═══════════════════════════════════════════════════════════════════════════ -->
    <?php
    $dev_posts   = civic_get_category_posts( 'development', 3 );
    $civic_posts = civic_get_category_posts( 'civic-governance', 3 );
    ?>
    <?php if ( $dev_posts || $civic_posts ) : ?>
    <section class="section section--dual" aria-label="Development and Governance">
        <div class="container">
            <div class="dual-grid">

                <?php if ( $dev_posts ) : ?>
                <div class="dual-grid__col">
                    <?php civic_section_header( 'Development Tracker', 'development' ); ?>
                    <div class="article-list">
                        <?php foreach ( $dev_posts as $post ) : ?>
                            <?php civic_article_card( $post, 'medium' ); ?>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <?php if ( $civic_posts ) : ?>
                <div class="dual-grid__col">
                    <?php civic_section_header( 'Civic Governance', 'civic-governance' ); ?>
                    <div class="article-list">
                        <?php foreach ( $civic_posts as $post ) : ?>
                            <?php civic_article_card( $post, 'medium' ); ?>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

            </div><!-- .dual-grid -->
        </div>
    </section>
    <?php endif; ?>

    <!-- ═══════════════════════════════════════════════════════════════════════
         TWO-COLUMN BAND: Public Notices + Schools & Education
    ═══════════════════════════════════════════════════════════════════════════ -->
    <?php
    $notices_posts = civic_get_category_posts( 'public-notices', 3 );
    $school_posts  = civic_get_category_posts( 'schools-education', 3 );
    ?>
    <?php if ( $notices_posts || $school_posts ) : ?>
    <section class="section section--dual" aria-label="Notices and Schools">
        <div class="container">
            <div class="dual-grid">

                <?php if ( $notices_posts ) : ?>
                <div class="dual-grid__col">
                    <?php civic_section_header( 'Public Notices', 'public-notices' ); ?>
                    <div class="article-list">
                        <?php foreach ( $notices_posts as $post ) : ?>
                            <?php civic_article_card( $post, 'small' ); ?>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

                <?php if ( $school_posts ) : ?>
                <div class="dual-grid__col">
                    <?php civic_section_header( 'Schools &amp; Education', 'schools-education' ); ?>
                    <div class="article-list">
                        <?php foreach ( $school_posts as $post ) : ?>
                            <?php civic_article_card( $post, 'small' ); ?>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endif; ?>

            </div>
        </div>
    </section>
    <?php endif; ?>

    <!-- ═══════════════════════════════════════════════════════════════════════
         FULL-WIDTH + SIDEBAR layout for Business + Meetings
    ═══════════════════════════════════════════════════════════════════════════ -->
    <div class="container">
        <div class="content-sidebar-wrap">

            <div class="content-main">

                <!-- New & Coming Soon (business licenses) -->
                <?php $biz_posts = civic_get_category_posts( 'business', 3 ); ?>
                <?php if ( $biz_posts ) : ?>
                <section class="section" aria-labelledby="biz-heading">
                    <?php civic_section_header( 'New &amp; Coming Soon', 'business' ); ?>
                    <div class="card-grid card-grid--3">
                        <?php foreach ( $biz_posts as $post ) : ?>
                            <?php civic_article_card( $post, 'small' ); ?>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Upcoming Meetings (most recent civic-governance articles) -->
                <?php $meeting_posts = civic_get_category_posts( 'civic-governance', 2 ); ?>
                <?php if ( $meeting_posts ) : ?>
                <section class="section" aria-labelledby="meetings-heading">
                    <?php civic_section_header( 'Upcoming Meetings', 'civic-governance' ); ?>
                    <div class="meetings-cards">
                        <?php foreach ( $meeting_posts as $post ) : ?>
                        <div class="meeting-card">
                            <div class="meeting-card__date">
                                <span class="meeting-card__month"><?php echo esc_html( get_the_date( 'M', $post ) ); ?></span>
                                <span class="meeting-card__day"><?php echo esc_html( get_the_date( 'j', $post ) ); ?></span>
                            </div>
                            <div class="meeting-card__info">
                                <h3 class="meeting-card__title">
                                    <a href="<?php echo esc_url( get_permalink( $post ) ); ?>">
                                        <?php echo esc_html( get_the_title( $post ) ); ?>
                                    </a>
                                </h3>
                                <p class="meeting-card__excerpt">
                                    <?php echo esc_html( wp_trim_words( get_the_excerpt( $post ), 20, '…' ) ); ?>
                                </p>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

            </div><!-- .content-main -->

            <aside class="content-sidebar" role="complementary">

                <!-- This Week in Numbers -->
                <section class="section">
                    <div class="section-header">
                        <h2 class="section-title">This Week in Numbers</h2>
                    </div>
                    <?php the_widget( 'Civic_Stats_Widget' ); ?>
                </section>

                <!-- About -->
                <section class="section">
                    <div class="section-header">
                        <h2 class="section-title">About <?php echo esc_html( $city ); ?></h2>
                    </div>
                    <?php the_widget( 'Civic_About_Widget' ); ?>
                </section>

                <?php if ( is_active_sidebar( 'sidebar-primary' ) ) : ?>
                    <?php dynamic_sidebar( 'sidebar-primary' ); ?>
                <?php endif; ?>

            </aside>

        </div><!-- .content-sidebar-wrap -->
    </div><!-- .container -->

</main><!-- #main -->

<?php get_footer(); ?>
