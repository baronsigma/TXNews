    </div><!-- #content -->

    <!-- ─── Site Footer ──────────────────────────────────────────────────── -->
    <footer id="colophon" class="site-footer" role="contentinfo">
        <div class="footer-inner container">

            <div class="footer-brand">
                <a class="footer-name" href="<?php echo esc_url( home_url( '/' ) ); ?>">
                    <?php echo esc_html( civic_publication_name() ); ?>
                </a>
                <p class="footer-tagline">
                    <?php echo esc_html( civic_city_name() ); ?>, Texas &mdash; Automated civic intelligence, published continuously.
                </p>
            </div>

            <?php if ( has_nav_menu( 'footer' ) ) : ?>
                <nav class="footer-nav" aria-label="<?php esc_attr_e( 'Footer', 'civic-record' ); ?>">
                    <?php wp_nav_menu( [
                        'theme_location' => 'footer',
                        'depth'          => 1,
                        'container'      => false,
                    ] ); ?>
                </nav>
            <?php endif; ?>

            <?php if ( is_active_sidebar( 'sidebar-footer' ) ) : ?>
                <div class="footer-widgets">
                    <?php dynamic_sidebar( 'sidebar-footer' ); ?>
                </div>
            <?php endif; ?>

        </div><!-- .footer-inner -->

        <div class="footer-legal container">
            <p>
                &copy; <?php echo esc_html( date_i18n( 'Y' ) ); ?>
                <?php echo esc_html( civic_publication_name() ); ?>.
                Content generated from public government data sources.
                Not affiliated with any government agency.
            </p>
            <p>
                Data: <a href="https://data.texas.gov/" target="_blank" rel="noopener noreferrer">Texas Open Data Portal</a>
                &bull; Powered by WordPress &amp; Ollama
            </p>
        </div>
    </footer><!-- #colophon -->

</div><!-- #page -->

<?php wp_footer(); ?>
</body>
</html>
