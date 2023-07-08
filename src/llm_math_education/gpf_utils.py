def get_gpd_codes(lesson_code):
    """
    Structure is: G<grade>.<domain><construct>.<subconstruct>.<skill>.<index>

    e.g. G9.N5.1.3.1 has:
        grade 9
        domain N
        construct N5
        subconstruct N5.1
        skill N5.1.3
        index 1
    """
    tokens = lesson_code.split(".")
    grade = int(tokens[0][1])
    index = int(tokens[-1])

    skill = ".".join(tokens[1:-1])

    domain = tokens[1][0]
    construct = tokens[1]
    subconstruct = tokens[1] + "." + tokens[2]
    return grade, domain, construct, subconstruct, skill, index
