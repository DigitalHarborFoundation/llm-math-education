import streamlit as st


def insert_textarea_with_selectbox(
    text_options: list[str],
    text_option_names: list[str],
    selectbox_label: str,
    key_prefix: str,
    custom_option_name: str = "Custom",
):
    """Generates a selectbox and textarea.

    Args:
        text_options (list[str]): Pre-defined strings that can be used in the textarea.
        text_option_names (list[str]): Selectbox option strings, corresponding to text_options.
        selectbox_label (str): Label for the selectbox.
        key_prefix (str): Key to use for the selectbox and textarea; should be app unique.
        custom_option_name (str, optional): Visible label for the "custom" option. Defaults to "Custom".

    Returns:
        selectbox_key, textarea_key: Keys that can be used to query the session state
    """
    assert len(text_options) == len(text_option_names), "Options and option names should be the same length."
    assert len(text_options) > 0, "Must provide at least one option."

    selectbox_key = key_prefix + "_selectbox"
    textarea_key = key_prefix + "_textarea"

    def selectbox_change():
        if st.session_state[selectbox_key] != custom_option_name:
            index = text_option_names.index(st.session_state[selectbox_key])
            st.session_state[textarea_key] = text_options[index]

    def textarea_change():
        if st.session_state[textarea_key] in text_options:
            index = text_options.index(st.session_state[textarea_key])
            st.session_state[selectbox_key] = text_option_names[index]
        elif st.session_state[selectbox_key] != custom_option_name:
            st.session_state[selectbox_key] = custom_option_name

    if textarea_key not in st.session_state:
        st.session_state[textarea_key] = text_options[0]
    if selectbox_key not in st.session_state:
        st.session_state[selectbox_key] = text_option_names[0]

    st.selectbox(
        selectbox_label,
        text_option_names + [custom_option_name],
        key=selectbox_key,
        on_change=selectbox_change,
    )
    st.text_area(
        selectbox_label + " text area",
        key=textarea_key,
        on_change=textarea_change,
        label_visibility="collapsed",
    )
    return selectbox_key, textarea_key
