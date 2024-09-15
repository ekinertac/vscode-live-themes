def human_format(num):
    num = float("{:.3g}".format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(
        "{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude]
    )


def get_quickpick_detail(theme_files_count, statistics):
    detail = f"$(symbol-color) {theme_files_count} {theme_files_count > 1 and 'Themes' or 'Theme'}"

    installs = statistics.get("installs", 0)
    rating = statistics.get("rating", 0)
    ratingcount = statistics.get("ratingcount", 0)

    if installs > 0:
        detail += f" | $(extensions-install-count) {human_format(installs)}"

    if rating > 0:
        detail += f" | $(star-full) {float("{:.1f}".format(rating))}"

    if ratingcount > 0:
        detail += f"/{human_format(ratingcount)}"

    return detail
