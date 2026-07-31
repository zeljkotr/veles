def create_plan(question):


    question = question.lower()


    remember_keywords = [

        "zapamti",
        "upamti",
        "seti se"

    ]


    has_remember = any(

        word in question

        for word in remember_keywords

    )


    if has_remember:


        return {

            "action": "remember_fact"

        }



    system_keywords = [

        "sistem",
        "server",
        "računar",
        "racunar",
        "cpu",
        "ram",
        "memorija",
        "disk",
        "stanje",
        "status"

    ]



    check_keywords = [

        "proveri",
        "provera",
        "pogledaj",
        "prikaži",
        "prikazi",
        "vidi",
        "kakvo je",
        "reci mi",
        "daj mi"

    ]



    has_system = any(

        word in question

        for word in system_keywords

    )



    has_check = any(

        word in question

        for word in check_keywords

    )



    if has_system and has_check:


        return {

            "action": "system_info"

        }



    return {

        "action": "chat"

    }