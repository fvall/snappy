

def tmp_suffix() -> str:
    return "---TMP-BK---"


def rotate_fwd(new: str, old: list, max: int = 0) -> list:

    if (max <= 0) or (len(old) < max):
        return [new] + old
    
    suffix = tmp_suffix()
    if max == 1:
        return [new, old[0] + suffix]
    
    output = [new] + old[:(max - 1)]
    output.append(old[max - 1] + suffix)
    return output


def rotate_bkd(llist: list) -> list:

    if not llist:
        return []
    
    suffix = tmp_suffix()
    last = llist[-1]
    output = list(llist)
    if last.endswith(suffix):
        output[-1] = output[-1].replace(suffix, "")
    
    return output
