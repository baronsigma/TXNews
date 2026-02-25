<?php get_header(); ?>

<div class="container">
    <div class="content-sidebar-wrap">

        <main id="main" class="site-main content-main" role="main">
            <?php while ( have_posts() ) : the_post(); ?>
            <article id="post-<?php the_ID(); ?>" <?php post_class( 'single-article' ); ?>>

                <header class="article-header">
                    <?php
                    $cats = get_the_category();
                    if ( $cats ) :
                        $cat = $cats[0];
                        ?>
                        <a href="<?php echo esc_url( get_category_link( $cat ) ); ?>" class="cat-badge">
                            <?php echo esc_html( $cat->name ); ?>
                        </a>
                    <?php endif; ?>
                    <h1 class="article-title"><?php the_title(); ?></h1>
                    <div class="article-meta">
                        <time datetime="<?php echo esc_attr( get_the_date( 'c' ) ); ?>">
                            <?php echo esc_html( get_the_date( 'F j, Y' ) ); ?>
                        </time>
                        <span class="article-meta__sep">&bull;</span>
                        <span><?php echo esc_html( civic_publication_name() ); ?></span>
                    </div>
                </header>

                <?php if ( has_post_thumbnail() ) : ?>
                    <figure class="article-featured-image">
                        <?php the_post_thumbnail( 'large', [ 'loading' => 'eager' ] ); ?>
                    </figure>
                <?php endif; ?>

                <div class="article-content entry-content">
                    <?php the_content(); ?>
                </div>

                <footer class="article-footer">
                    <p class="article-disclosure">
                        This article was generated automatically from public government data sources
                        using a local language model. Source: <?php echo esc_html( civic_publication_name() ); ?>,
                        <?php echo esc_html( civic_city_name() ); ?>, Texas.
                    </p>
                    <?php
                    $tags = get_the_tags();
                    if ( $tags ) :
                        ?>
                        <div class="article-tags">
                            <?php foreach ( $tags as $tag ) : ?>
                                <a href="<?php echo esc_url( get_tag_link( $tag ) ); ?>" class="tag-link">
                                    #<?php echo esc_html( $tag->name ); ?>
                                </a>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </footer>

            </article>

            <!-- Related posts in same category -->
            <?php
            $related = civic_get_category_posts(
                get_the_category()[0]->slug ?? '',
                3
            );
            $related = array_filter( $related, fn( $p ) => $p->ID !== get_the_ID() );
            $related = array_slice( $related, 0, 3 );
            if ( $related ) :
                ?>
                <section class="related-posts">
                    <div class="section-header">
                        <h2 class="section-title">More from <?php echo esc_html( civic_city_name() ); ?></h2>
                    </div>
                    <div class="card-grid card-grid--3">
                        <?php foreach ( $related as $rel_post ) : ?>
                            <?php civic_article_card( $rel_post, 'small' ); ?>
                        <?php endforeach; ?>
                    </div>
                </section>
            <?php endif; ?>

            <?php endwhile; ?>
        </main>

        <aside class="content-sidebar" role="complementary">
            <?php get_sidebar(); ?>
        </aside>

    </div>
</div>

<?php get_footer(); ?>
