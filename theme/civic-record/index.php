<?php
/**
 * index.php — fallback template (blog listing)
 * Used when no more specific template matches.
 */

get_header();
?>

<div class="container">
    <div class="content-sidebar-wrap">

        <main id="main" class="site-main content-main" role="main">

            <?php if ( have_posts() ) : ?>
                <div class="article-list">
                    <?php while ( have_posts() ) : the_post(); ?>
                        <?php civic_article_card( get_post(), 'medium' ); ?>
                    <?php endwhile; ?>
                </div>
                <?php the_posts_pagination(); ?>
            <?php else : ?>
                <p class="no-posts"><?php esc_html_e( 'Nothing to show yet — check back soon.', 'civic-record' ); ?></p>
            <?php endif; ?>

        </main>

        <aside class="content-sidebar" role="complementary">
            <?php get_sidebar(); ?>
        </aside>

    </div>
</div>

<?php get_footer(); ?>
