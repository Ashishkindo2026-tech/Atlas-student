from tools.system_tools import (
    get_time,
    get_date,
    open_notepad,
    open_calculator,
    open_google,
    open_youtube
)


def execute(user):

    text = user.lower()

    if "time" in text:
        return get_time()

    if "date" in text:
        return get_date()

    if "open notepad" in text:
        open_notepad()
        return "Opening Notepad."

    if "open calculator" in text:
        open_calculator()
        return "Opening Calculator."

    if "open google" in text:
        open_google()
        return "Opening Google."

    if "open youtube" in text:
        open_youtube()
        return "Opening YouTube."

    return None