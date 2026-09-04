cd ~/veles

cat > veles/web/static/js/veles.js <<'EOF'
document.addEventListener(
    "DOMContentLoaded",
    function () {


        const form =
            document.getElementById(
                "chat-form"
            );


        const textarea =
            document.getElementById(
                "question"
            );


        const newChatButton =
            document.getElementById(
                "new-chat-button"
            );


        const voiceButton =
            document.getElementById(
                "voice-button"
            );


        const overlay =
            document.getElementById(
                "thinking-overlay"
            );


        const powerButton =
            document.getElementById(
                "power-button"
            );


        const powerMenu =
            document.getElementById(
                "power-menu"
            );


        const rebootButton =
            document.getElementById(
                "power-reboot"
            );


        const shutdownButton =
            document.getElementById(
                "power-shutdown"
            );


        /*
        ENTER = SEND
        SHIFT + ENTER = NOVI RED
        */

        if (textarea && form) {

            textarea.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter"
                        &&
                        !event.shiftKey
                    ) {

                        event.preventDefault();

                        form.requestSubmit();

                    }

                }
            );

        }


        /*
        SUBMIT - PRIKAŽI VELES RAZMIŠLJANJE
        */

        if (form) {

            form.addEventListener(
                "submit",
                function () {

                    if (overlay) {

                        overlay.style.display =
                            "flex";

                    }

                }
            );

        }


        /*
        NOVI RAZGOVOR
        */

        if (newChatButton) {

            newChatButton.addEventListener(
                "click",
                function () {

                    window.location.href =
                        "/chat?new=1";

                }
            );

        }


        /*
        VOICE DUGME
        */

        if (voiceButton) {

            voiceButton.addEventListener(
                "click",
                function () {

                    alert(
                        "Voice funkcija uskoro."
                    );

                }
            );

        }


        /*
        POWER MENU
        */

        function closePowerMenu() {

            if (!powerMenu || !powerButton) {
                return;
            }

            powerMenu.classList.remove(
                "open"
            );

            powerMenu.setAttribute(
                "aria-hidden",
                "true"
            );

            powerButton.setAttribute(
                "aria-expanded",
                "false"
            );

        }


        function togglePowerMenu() {

            if (!powerMenu || !powerButton) {
                return;
            }

            const isOpen =
                powerMenu.classList.contains(
                    "open"
                );


            if (isOpen) {

                closePowerMenu();

                return;

            }


            powerMenu.classList.add(
                "open"
            );

            powerMenu.setAttribute(
                "aria-hidden",
                "false"
            );

            powerButton.setAttribute(
                "aria-expanded",
                "true"
            );

        }


        if (powerButton) {

            powerButton.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();

                    togglePowerMenu();

                }
            );

        }


        document.addEventListener(
            "click",
            function (event) {

                if (
                    powerMenu
                    &&
                    powerButton
                    &&
                    !powerMenu.contains(event.target)
                    &&
                    !powerButton.contains(event.target)
                ) {

                    closePowerMenu();

                }

            }
        );


        /*
        POWER ACTIONS

        Backend akcije se povezuju
        u sledećoj fazi.
        */

        if (rebootButton) {

            rebootButton.addEventListener(
                "click",
                function () {

                    alert(
                        "VELES REBOOT action will be connected next."
                    );

                }
            );

        }


        if (shutdownButton) {

            shutdownButton.addEventListener(
                "click",
                function () {

                    alert(
                        "VELES SHUTDOWN action will be connected next."
                    );

                }
            );

        }


    }
);
EOF