from app.bot import constants


def get_checkbox(selected: bool) -> str:
    """Get a checkbox text based on its state"""

    return constants.CHECKED_CHECKBOX if selected else constants.UNCHECKED_CHECKBOX
