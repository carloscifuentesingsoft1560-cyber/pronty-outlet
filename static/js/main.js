document.addEventListener(
    "DOMContentLoaded",
    () => {

        // ====================================================
        // MENÚ HAMBURGUESA
        // ====================================================

        const menuToggle = document.querySelector(
            ".site-header__menu-toggle"
        );

        const mainNav = document.querySelector(
            ".main-nav"
        );


        function refreshLucideIcons() {

            if (
                typeof lucide !== "undefined"
            ) {

                lucide.createIcons();

            }

        }


        function closeMobileMenu() {

            if (
                !menuToggle
                || !mainNav
            ) {

                return;

            }


            mainNav.classList.remove(
                "main-nav--open"
            );


            menuToggle.setAttribute(
                "aria-expanded",
                "false"
            );


            menuToggle.setAttribute(
                "aria-label",
                "Abrir menú de categorías"
            );


            const icon = menuToggle.querySelector(
                "[data-lucide]"
            );


            if (icon) {

                icon.setAttribute(
                    "data-lucide",
                    "menu"
                );

            }


            refreshLucideIcons();

        }


        function openMobileMenu() {

            if (
                !menuToggle
                || !mainNav
            ) {

                return;

            }


            mainNav.classList.add(
                "main-nav--open"
            );


            menuToggle.setAttribute(
                "aria-expanded",
                "true"
            );


            menuToggle.setAttribute(
                "aria-label",
                "Cerrar menú de categorías"
            );


            const icon = menuToggle.querySelector(
                "[data-lucide]"
            );


            if (icon) {

                icon.setAttribute(
                    "data-lucide",
                    "x"
                );

            }


            refreshLucideIcons();

        }


        if (
            menuToggle
            && mainNav
        ) {

            menuToggle.addEventListener(
                "click",
                () => {

                    const isOpen = (
                        mainNav.classList.contains(
                            "main-nav--open"
                        )
                    );


                    if (isOpen) {

                        closeMobileMenu();

                    } else {

                        openMobileMenu();

                    }

                }
            );


            document.addEventListener(
                "keydown",
                (event) => {

                    if (
                        event.key === "Escape"
                    ) {

                        closeMobileMenu();

                    }

                }
            );


            window.addEventListener(
                "resize",
                () => {

                    if (
                        window.innerWidth > 980
                    ) {

                        closeMobileMenu();

                    }

                }
            );

        }


        // ====================================================
        // CONTADOR DEL LIVE
        // ====================================================

        const countdown = document.querySelector(
            ".live-countdown"
        );


        if (!countdown) {

            return;

        }


        // Fecha de ejemplo del próximo Live.
        // Más adelante esta fecha vendrá desde el panel
        // del administrador.

        const liveDate = new Date(
            "2026-09-06T20:00:00"
        );


        const units = countdown.querySelectorAll(
            "strong"
        );


        function updateCountdown() {

            const now = new Date();

            const difference = (
                liveDate - now
            );


            if (difference <= 0) {

                units[0].textContent = "00";
                units[1].textContent = "00";
                units[2].textContent = "00";
                units[3].textContent = "00";

                return;

            }


            const days = Math.floor(
                difference
                / (
                    1000
                    * 60
                    * 60
                    * 24
                )
            );


            const hours = Math.floor(
                (
                    difference
                    / (
                        1000
                        * 60
                        * 60
                    )
                )
                % 24
            );


            const minutes = Math.floor(
                (
                    difference
                    / (
                        1000
                        * 60
                    )
                )
                % 60
            );


            const seconds = Math.floor(
                (
                    difference
                    / 1000
                )
                % 60
            );


            units[0].textContent = (
                String(days)
                .padStart(
                    2,
                    "0"
                )
            );

            units[1].textContent = (
                String(hours)
                .padStart(
                    2,
                    "0"
                )
            );

            units[2].textContent = (
                String(minutes)
                .padStart(
                    2,
                    "0"
                )
            );

            units[3].textContent = (
                String(seconds)
                .padStart(
                    2,
                    "0"
                )
            );

        }


        updateCountdown();


        setInterval(
            updateCountdown,
            1000
        );

    }
);