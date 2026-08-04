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



    }
);