/*
    VELES OPERATIONS MAP

    Dynamic connection engine

    Crta veze između VELES centra
    i svih modula.
*/


function updateVelesConnections() {


    const map = document.querySelector(
        ".operations-map"
    );


    const svg = document.querySelector(
        ".connection-lines"
    );


    const core = document.querySelector(
        ".core"
    );


    if (!map || !svg || !core) {

        return;

    }



    const mapRect =
        map.getBoundingClientRect();



    const coreRect =
        core.getBoundingClientRect();



    const centerX =
        coreRect.left -
        mapRect.left +
        coreRect.width / 2;



    const centerY =
        coreRect.top -
        mapRect.top +
        coreRect.height / 2;





    const lines =
        svg.querySelectorAll(
            ".data-line"
        );




    lines.forEach(
        line => {


            const targetName =
                line.dataset.target;



            const target =
                document.querySelector(
                    "." + targetName
                );



            if (!target) {

                return;

            }




            const targetRect =
                target.getBoundingClientRect();




            const targetX =
                targetRect.left -
                mapRect.left +
                targetRect.width / 2;



            const targetY =
                targetRect.top -
                mapRect.top +
                targetRect.height / 2;




            line.setAttribute(
                "x1",
                centerX
            );



            line.setAttribute(
                "y1",
                centerY
            );



            line.setAttribute(
                "x2",
                targetX
            );



            line.setAttribute(
                "y2",
                targetY
            );


        }
    );


}





function initVelesDashboard(){


    updateVelesConnections();


    window.addEventListener(
        "resize",
        updateVelesConnections
    );


    setInterval(
        updateVelesConnections,
        2000
    );


}





document.addEventListener(
    "DOMContentLoaded",
    initVelesDashboard
);