/*
    VELES WEB JAVASCRIPT
*/


document.addEventListener(
    "DOMContentLoaded",
    function(){


        const textarea =
            document.getElementById(
                "question"
            );


        const form =
            document.getElementById(
                "chat-form"
            );


        const overlay =
            document.getElementById(
                "thinking-overlay"
            );



        /*
        ENTER SEND
        */

        if(textarea && form){

            textarea.addEventListener(
                "keydown",
                function(event){


                    if(
                        event.key === "Enter" &&
                        !event.shiftKey
                    ){

                        event.preventDefault();

                        form.submit();

                    }

                }
            );

        }



        /*
        THINKING OVERLAY
        */

        if(form && overlay){

            form.addEventListener(
                "submit",
                function(){

                    overlay.style.display =
                        "flex";

                }
            );

        }



        /*
        AUTO SCROLL
        */

        const history =
            document.getElementById(
                "chat-history"
            );


        if(history){

            history.scrollTop =
                history.scrollHeight;

        }



        /*
        VOICE
        */

        const voiceButton =
            document.getElementById(
                "voice-button"
            );


        if(voiceButton){

            voiceButton.onclick =
                function(){

                    voiceButton.innerHTML =
                        "🎙 Aktivacija...";

                };

        }



        /*
        NEW CHAT
        */

        const newChatButton =
            document.getElementById(
                "new-chat-button"
            );


        if(newChatButton){

            newChatButton.onclick =
                function(){

                    location.reload();

                };

        }


    }
);