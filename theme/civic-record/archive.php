<?php get_header(); ?>

<div class="container">
    <div class="content-sidebar-wrap">

        <main id="main" class="site-main content-main" role="main">

            <header class="archive-header">
                <?php
                if ( is_category() ) :
                    $cat = get_queried_object();
                    echo '<a class="cat-badge" href="#">' . esc_html( $cat->name ) . '</a>';
                    echo '<h1 class="archive-title">' . esc_html( $cat->name ) . ' in ' . esc_html( civic_city_name() ) . '</h1>';
                    if ( $cat->description ) :
                        echo '<p class="archive-description">' . esc_html( $cat->description ) . '</p>';
                    endif;
                elseif ( is_tag() ) :
                    echo '<h1 class="archive-title">Tagged: ' . esc_html( single_tag_title( '', false ) ) . '</h1>';
                elseif ( is_date() ) :
                    echo '<h1 class="archive-title">' . esc_html( get_the_date( 'F Y' ) ) . '</h1>';
                else :
                    echo '<h1 class="archive-title">' . esc_html__( 'Archives', 'civic-record' ) . '</h1>';
                endif;
                ?>
            </header>

            <?php if ( have_posts() ) : ?>
                <div class="article-list article-list--archive">
                    <?php while ( have_posts() ) : the_post(); ?>
                        <?php civic_article_card( get_post(), 'medium' ); ?>
                    <?php endwhile; ?>
                </div>

                <?php the_posts_pagination( [
                    'prev_text' => '&larr; Older',
                    'next_text' => 'Newer &rarr;',
                ] ); ?>

            <?php else : ?>
                <p class="no-posts"><?php esc_html_e( 'No articles found.', 'civic-record' ); ?></p>
            <?php endif; ?>

        </main>

        <aside class="content-sidebar" role="complementary">
            <?php get_sidebar(); ?>
        </aside>

    </div>
</div>

<?php get_footer(); ?>
