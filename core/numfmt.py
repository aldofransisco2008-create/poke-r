"""Number formatting for scores that run from hundreds up to 1E234."""

SUFFIX = ("", "K", "M", "B", "T")


def fmt_num(n):
    """1,234 | 1.23M | 4.56B | 7.89T | 1.23E15 ... 1.00E234 (works on huge ints and floats)."""
    n = int(n)
    if n < 10 ** 6:
        return f"{n:,}"
    s = str(n)
    exp = len(s) - 1
    if exp < 15:
        g = exp % 3
        return f"{s[:g + 1]}.{s[g + 1:g + 3]}{SUFFIX[exp // 3]}"
    return f"{s[0]}.{s[1:3]}E{exp}"
