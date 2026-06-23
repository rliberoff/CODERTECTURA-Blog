(() => {
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const revealItems = [...document.querySelectorAll('[data-reveal]')];
    const parallaxItems = [...document.querySelectorAll('[data-parallax]')];
    const header = document.querySelector('[data-site-header]');
    const scrollCue = document.querySelector('[data-scroll-cue]');
    const featuredPosts = document.querySelector('#latest-posts');
    const cookieBanner = document.querySelector('[data-cookie-banner]');
    const cookieAccept = document.querySelector('[data-cookie-accept]');
    const contentEmbeds = [...document.querySelectorAll('.content > iframe, .content > video, .content p > iframe, .content p > video')];
    const lightboxLinks = [...document.querySelectorAll('[data-lightbox-image]')];
    const cookieConsentKey = 'codertectura-cookie-consent';

    if (cookieBanner && window.localStorage?.getItem(cookieConsentKey) !== 'accepted') {
        cookieBanner.hidden = false;
    }

    cookieAccept?.addEventListener('click', () => {
        window.localStorage?.setItem(cookieConsentKey, 'accepted');
        cookieBanner?.setAttribute('hidden', '');
    });

    contentEmbeds.forEach((embed) => {
        if (embed.closest('.responsive-embed, .legacy-embed')) {
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'legacy-embed';
        embed.parentNode.insertBefore(wrapper, embed);
        wrapper.appendChild(embed);
    });

    if (lightboxLinks.length) {
        let lastFocusedElement = null;
        let closeTimer = 0;
        let currentLightboxLinks = [];
        let currentLightboxIndex = -1;
        const focusableSelector = [
            'a[href]',
            'area[href]',
            'button:not([disabled])',
            'input:not([disabled]):not([type="hidden"])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            'iframe',
            'object',
            'embed',
            '[contenteditable]:not([contenteditable="false"])',
            '[tabindex]:not([tabindex="-1"])'
        ].join(',');

        const lightbox = document.createElement('div');
        lightbox.className = 'post-image-lightbox';
        lightbox.hidden = true;
        lightbox.tabIndex = -1;
        lightbox.setAttribute('role', 'dialog');
        lightbox.setAttribute('aria-modal', 'true');
        lightbox.setAttribute('aria-label', 'Imagen ampliada');

        lightbox.innerHTML = `
            <button class="post-image-lightbox__close" type="button" aria-label="Cerrar imagen ampliada" data-lightbox-close>
                <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">
                    <path d="M18 6 6 18" />
                    <path d="m6 6 12 12" />
                </svg>
            </button>
            <button class="post-image-lightbox__nav post-image-lightbox__nav--prev" type="button" aria-label="Ver imagen anterior" data-lightbox-prev hidden>‹</button>
            <button class="post-image-lightbox__nav post-image-lightbox__nav--next" type="button" aria-label="Ver imagen siguiente" data-lightbox-next hidden>›</button>
            <figure class="post-image-lightbox__content">
                <img class="post-image-lightbox__image" alt="">
                <figcaption class="post-image-lightbox__caption" id="post-image-lightbox-caption" hidden></figcaption>
            </figure>
        `;

        document.body.appendChild(lightbox);

        const lightboxImage = lightbox.querySelector('.post-image-lightbox__image');
        const lightboxCaption = lightbox.querySelector('.post-image-lightbox__caption');
        const lightboxClose = lightbox.querySelector('[data-lightbox-close]');
        const lightboxPrev = lightbox.querySelector('[data-lightbox-prev]');
        const lightboxNext = lightbox.querySelector('[data-lightbox-next]');

        const getFocusableElements = () => [...lightbox.querySelectorAll(focusableSelector)]
            .filter((element) => !element.hidden && element.tabIndex >= 0 && element.getClientRects().length > 0);

        const withInstantScroll = (callback) => {
            const root = document.documentElement;
            const previousScrollBehavior = root.style.getPropertyValue('scroll-behavior');
            const previousScrollBehaviorPriority = root.style.getPropertyPriority('scroll-behavior');

            root.style.setProperty('scroll-behavior', 'auto', 'important');

            try {
                callback();
            } finally {
                if (previousScrollBehavior) {
                    root.style.setProperty('scroll-behavior', previousScrollBehavior, previousScrollBehaviorPriority);
                } else {
                    root.style.removeProperty('scroll-behavior');
                }
            }
        };

        const focusWithoutScrolling = (element) => {
            if (!(element instanceof HTMLElement) || !element.isConnected) {
                return;
            }

            const scrollX = window.scrollX || window.pageXOffset || 0;
            const scrollY = window.scrollY || window.pageYOffset || 0;

            withInstantScroll(() => {
                try {
                    element.focus({ preventScroll: true });
                } catch {
                    element.focus();
                }

                window.scrollTo(scrollX, scrollY);
            });
        };

        const lockScroll = () => {
            const scrollX = window.scrollX || window.pageXOffset || 0;
            const scrollY = window.scrollY || window.pageYOffset || 0;
            document.body.dataset.lightboxScrollX = `${scrollX}`;
            document.body.dataset.lightboxScrollY = `${scrollY}`;
            document.body.style.left = `-${scrollX}px`;
            document.body.style.top = `-${scrollY}px`;
            document.body.classList.add('is-lightbox-open');
        };

        const unlockScroll = () => {
            const scrollX = Number.parseInt(document.body.dataset.lightboxScrollX || '0', 10) || 0;
            const scrollY = Number.parseInt(document.body.dataset.lightboxScrollY || '0', 10);
            const safeScrollY = Number.isFinite(scrollY) ? scrollY : 0;

            withInstantScroll(() => {
                document.body.classList.remove('is-lightbox-open');
                document.body.style.removeProperty('left');
                document.body.style.removeProperty('top');
                delete document.body.dataset.lightboxScrollX;
                delete document.body.dataset.lightboxScrollY;
                window.scrollTo(scrollX, safeScrollY);
            });
        };

        const getGroupLinks = (link) => {
            const group = link.dataset.lightboxGroup || 'default';
            return lightboxLinks.filter((candidate) => (candidate.dataset.lightboxGroup || 'default') === group);
        };

        const updateNavigation = () => {
            const hasMultipleItems = currentLightboxLinks.length > 1;
            lightboxPrev.hidden = !hasMultipleItems;
            lightboxNext.hidden = !hasMultipleItems;
        };

        const navigateLightbox = (direction) => {
            if (!currentLightboxLinks.length) {
                return;
            }

            currentLightboxIndex = (currentLightboxIndex + direction + currentLightboxLinks.length) % currentLightboxLinks.length;
            openLightbox(currentLightboxLinks[currentLightboxIndex], { preserveFocus: true });
        };

        const closeLightbox = () => {
            if (!lightbox.classList.contains('is-open')) {
                return;
            }

            lightbox.classList.remove('is-open');
            unlockScroll();
            focusWithoutScrolling(lastFocusedElement);

            closeTimer = window.setTimeout(() => {
                lightbox.hidden = true;
                lightboxImage.removeAttribute('src');
            }, 180);
        };

        const openLightbox = (link, options = {}) => {
            window.clearTimeout(closeTimer);
            const sourceImage = link.querySelector('img');
            const caption = link.closest('.content-figure')?.querySelector('figcaption')?.textContent.trim()
                || link.closest('.content-gallery')?.querySelector('figcaption')?.textContent.trim()
                || '';

            if (!options.preserveFocus) {
                lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
            }

            currentLightboxLinks = getGroupLinks(link);
            currentLightboxIndex = currentLightboxLinks.indexOf(link);

            if (currentLightboxIndex < 0) {
                currentLightboxLinks = [link];
                currentLightboxIndex = 0;
            }

            updateNavigation();
            lightboxImage.src = link.href;
            lightboxImage.alt = sourceImage?.alt || 'Imagen ampliada';
            lightboxCaption.textContent = caption;
            lightboxCaption.hidden = !caption;

            if (caption) {
                lightbox.setAttribute('aria-describedby', 'post-image-lightbox-caption');
            } else {
                lightbox.removeAttribute('aria-describedby');
            }

            lockScroll();
            lightbox.hidden = false;

            window.requestAnimationFrame(() => {
                lightbox.classList.add('is-open');
                lightboxClose.focus({ preventScroll: true });
            });
        };

        lightboxPrev.addEventListener('click', () => {
            navigateLightbox(-1);
        });

        lightboxNext.addEventListener('click', () => {
            navigateLightbox(1);
        });

        lightboxLinks.forEach((link) => {
            link.addEventListener('click', (event) => {
                if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
                    return;
                }

                event.preventDefault();
                openLightbox(link);
            });
        });

        lightbox.addEventListener('click', (event) => {
            if (event.target === lightbox || event.target.closest('[data-lightbox-close]')) {
                closeLightbox();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (!lightbox.classList.contains('is-open')) {
                return;
            }

            if (event.key === 'Escape') {
                event.preventDefault();
                closeLightbox();
                return;
            }

            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                navigateLightbox(-1);
                return;
            }

            if (event.key === 'ArrowRight') {
                event.preventDefault();
                navigateLightbox(1);
                return;
            }

            if (event.key === 'Tab') {
                const focusableElements = getFocusableElements();

                if (!focusableElements.length) {
                    event.preventDefault();
                    lightbox.focus({ preventScroll: true });
                    return;
                }

                const firstFocusableElement = focusableElements[0];
                const lastFocusableElement = focusableElements[focusableElements.length - 1];
                const activeElement = document.activeElement;

                if (!focusableElements.includes(activeElement)) {
                    event.preventDefault();
                    (event.shiftKey ? lastFocusableElement : firstFocusableElement).focus({ preventScroll: true });
                    return;
                }

                if (event.shiftKey && activeElement === firstFocusableElement) {
                    event.preventDefault();
                    lastFocusableElement.focus({ preventScroll: true });
                    return;
                }

                if (!event.shiftKey && activeElement === lastFocusableElement) {
                    event.preventDefault();
                    firstFocusableElement.focus({ preventScroll: true });
                }
            }
        });
    }

    const revealAll = () => revealItems.forEach((item) => item.classList.add('is-visible'));

    if (motionQuery.matches || !('IntersectionObserver' in window)) {
        revealAll();
    } else {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.14 });

        revealItems.forEach((item) => observer.observe(item));
    }

    const hideScrollCue = () => scrollCue?.classList.add('is-hidden');
    const showScrollCue = () => scrollCue?.classList.remove('is-hidden');

    if (scrollCue && featuredPosts) {
        // Show the cue only when no meaningful card content is visible on first
        // paint. "Meaningful" = at least 20 % of the first card is in the
        // viewport.  A card whose top edge barely creeps into the bottom of the
        // screen (e.g. at 125 % browser zoom) does NOT count.
        setTimeout(() => {
            const firstCard = featuredPosts.querySelector('.post-card') || featuredPosts;
            const rect = firstCard.getBoundingClientRect();
            const visiblePx = Math.max(0, Math.min(window.innerHeight, rect.bottom) - Math.max(0, rect.top));
            const postsInView = rect.height > 0 && (visiblePx / rect.height) >= 0.2;

            if (!postsInView) {
                showScrollCue();

                // Hide once 20 % of the first card enters the viewport (mirrors
                // the threshold used above so the observer never fires on the
                // first paint that triggered the cue).
                if ('IntersectionObserver' in window) {
                    const io = new IntersectionObserver((entries) => {
                        if (entries[0].isIntersecting) {
                            hideScrollCue();
                            io.disconnect();
                        }
                    }, { threshold: 0.2 });
                    io.observe(firstCard);
                }

                // Also hide on first scroll
                window.addEventListener('scroll', hideScrollCue, { passive: true, once: true });

                scrollCue.addEventListener('click', (e) => {
                    e.preventDefault();
                    const target = featuredPosts.getBoundingClientRect().top + window.scrollY - (window.innerHeight * 0.05);
                    window.scrollTo({ top: Math.max(0, target), behavior: 'smooth' });
                    hideScrollCue();
                });
            }
        }, 80);
    }

    let ticking = false;

    const updateScrollEffects = () => {
        const y = window.scrollY || 0;

        if (header) {
            header.classList.toggle('is-scrolled', y > 16);
        }



        if (!motionQuery.matches) {
            parallaxItems.forEach((item) => {
                const rect = item.getBoundingClientRect();
                const offset = Math.round(rect.top * -0.035);
                item.style.setProperty('--parallax-offset', `${offset}px`);
            });
        }

        ticking = false;
    };

    const requestScrollEffects = () => {
        if (!ticking) {
            window.requestAnimationFrame(updateScrollEffects);
            ticking = true;
        }
    };

    updateScrollEffects();
    window.addEventListener('scroll', requestScrollEffects, { passive: true });

    motionQuery.addEventListener?.('change', (event) => {
        if (event.matches) {
            revealAll();
            parallaxItems.forEach((item) => item.style.removeProperty('--parallax-offset'));
        }
    });
})();
