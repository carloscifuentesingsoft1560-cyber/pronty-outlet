document.addEventListener(
    "DOMContentLoaded",
    () => {

        // ====================================================
        // ICONOS LUCIDE
        // ====================================================

        function refreshLucideIcons() {

            if (
                typeof lucide !== "undefined"
            ) {

                lucide.createIcons();

            }

        }


        // ====================================================
        // MENÚ HAMBURGUESA
        // ====================================================

        const menuToggle = document.querySelector(
            ".site-header__menu-toggle"
        );

        const mainNav = document.querySelector(
            ".main-nav"
        );


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
        // MODAL DE CORREO
        // ====================================================

        const emailModal = document.getElementById(
            "pronty-email-modal"
        );

        const emailOpenButton = document.getElementById(
            "contact-email-open"
        );

        const emailCloseButtons = document.querySelectorAll(
            "[data-email-close]"
        );

        const emailSubject = document.getElementById(
            "contact-email-subject"
        );

        const emailMessage = document.getElementById(
            "contact-email-message"
        );

        const emailGmailButton = document.getElementById(
            "contact-email-gmail"
        );

        const emailCopyButton = document.getElementById(
            "contact-email-copy"
        );

        const emailFeedback = document.getElementById(
            "contact-email-feedback"
        );

        const prontyEmail = (
            "prontyoutlet@gmail.com"
        );


        function openEmailModal() {

            if (!emailModal) {

                return;

            }


            emailModal.classList.add(
                "pronty-email-modal--open"
            );


            emailModal.setAttribute(
                "aria-hidden",
                "false"
            );


            document.body.classList.add(
                "pronty-modal-open"
            );


            if (emailSubject) {

                window.setTimeout(
                    () => {

                        emailSubject.focus();

                    },
                    100
                );

            }

        }


        function closeEmailModal() {

            if (!emailModal) {

                return;

            }


            emailModal.classList.remove(
                "pronty-email-modal--open"
            );


            emailModal.setAttribute(
                "aria-hidden",
                "true"
            );


            document.body.classList.remove(
                "pronty-modal-open"
            );


            if (emailFeedback) {

                emailFeedback.textContent = "";

            }

        }


        if (
            emailOpenButton
            && emailModal
        ) {

            emailOpenButton.addEventListener(
                "click",
                openEmailModal
            );

        }


        emailCloseButtons.forEach(
            (button) => {

                button.addEventListener(
                    "click",
                    closeEmailModal
                );

            }
        );


        if (emailCopyButton) {

            emailCopyButton.addEventListener(
                "click",
                async () => {

                    try {

                        await navigator.clipboard.writeText(
                            prontyEmail
                        );


                        if (emailFeedback) {

                            emailFeedback.textContent = (
                                "Correo copiado."
                            );

                        }

                    } catch (error) {

                        if (emailFeedback) {

                            emailFeedback.textContent = (
                                "Correo: "
                                + prontyEmail
                            );

                        }

                    }

                }
            );

        }


        if (emailGmailButton) {

            emailGmailButton.addEventListener(
                "click",
                () => {

                    const subject = (
                        emailSubject
                        ? emailSubject.value.trim()
                        : ""
                    );


                    const message = (
                        emailMessage
                        ? emailMessage.value.trim()
                        : ""
                    );


                    if (!subject) {

                        if (emailFeedback) {

                            emailFeedback.textContent = (
                                "Escribe el asunto del correo."
                            );

                        }


                        if (emailSubject) {

                            emailSubject.focus();

                        }


                        return;

                    }


                    if (!message) {

                        if (emailFeedback) {

                            emailFeedback.textContent = (
                                "Escribe el mensaje que deseas enviar."
                            );

                        }


                        if (emailMessage) {

                            emailMessage.focus();

                        }


                        return;

                    }


                    if (emailFeedback) {

                        emailFeedback.textContent = "";

                    }


                    const gmailUrl = (
                        "https://mail.google.com/mail/"
                        + "?view=cm"
                        + "&fs=1"
                        + "&to="
                        + encodeURIComponent(
                            prontyEmail
                        )
                        + "&su="
                        + encodeURIComponent(
                            subject
                        )
                        + "&body="
                        + encodeURIComponent(
                            message
                        )
                    );


                    window.open(
                        gmailUrl,
                        "_blank",
                        "noopener,noreferrer"
                    );

                }
            );

        }


        // ====================================================
        // ESC
        // ====================================================

        document.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key !== "Escape"
                ) {

                    return;

                }


                closeMobileMenu();

                closeEmailModal();

            }
        );


        // ====================================================
        // CONTADOR REAL DE PRONTY LIVE
        // ====================================================

        const countdown = document.querySelector(
            ".live-countdown[data-live-target]"
        );


        if (!countdown) {

            return;

        }


        const liveTarget = countdown.getAttribute(
            "data-live-target"
        );


        if (!liveTarget) {

            return;

        }


        const liveDate = new Date(
            liveTarget
        );


        if (
            Number.isNaN(
                liveDate.getTime()
            )
        ) {

            return;

        }


        const units = countdown.querySelectorAll(
            "strong"
        );


        if (
            units.length < 4
        ) {

            return;

        }


        let countdownInterval = null;


        function setCountdownToZero() {

            units[0].textContent = "00";
            units[1].textContent = "00";
            units[2].textContent = "00";
            units[3].textContent = "00";

        }


        function updateCountdown() {

            const now = new Date();


            const difference = (
                liveDate.getTime()
                - now.getTime()
            );


            if (
                difference <= 0
            ) {

                setCountdownToZero();


                if (countdownInterval) {

                    window.clearInterval(
                        countdownInterval
                    );

                }


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


        countdownInterval = window.setInterval(
            updateCountdown,
            1000
        );

    }
);