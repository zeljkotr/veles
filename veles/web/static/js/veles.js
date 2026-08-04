/*
    VELES WEB JAVASCRIPT

    Funkcije:
    - Enter slanje poruke
    - Shift+Enter novi red
    - Thinking overlay
    - Auto scroll chat
*/


document.addEventListener(
    "DOMContentLoaded",
    function(){


        const textarea = document.getElementById(
            "question"
        );


        const form = document.getElementById(
            "chat-form"
        );


        const overlay = document.getElementById(
            "thinking-overlay"
        );




        if(textarea && form){


            textarea.addEventListener(
                "keydown",
                function(event){


                    if(
                        event.key === "Enter" &&
                        !event.shiftKey
                    ){


                        event.preventDefault();


                        form.requestSubmit();


                    }


                }
            );


        }





        if(form && overlay){


            form.addEventListener(
                "submit",
                function(){


                    overlay.style.display = "flex";


                }
            );


        }






        const history = document.getElementById(
            "chat-history"
        );


        if(history){


            history.scrollTop =
                history.scrollHeight;


        }



    }
);