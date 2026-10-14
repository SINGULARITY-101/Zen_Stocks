# Shared helpers for turning price data into SVG coordinates.
# Used by BOTH the sidebar sparklines (small box) and the stock detail chart (big box)


def build_polyline_points(closes, width, height, padding = 0) : 
    """
    Converts a list of closing prices into an SVG <polyline points="..."> string, scaled to fit a width x height box.
    padding shrinks the drawable area inward on all sides, leaving a margin
    Returns None if there isn't enough data to draw a line (need at least 2 points).
    """
    
    # A line needs at least 2 points; with 0 or 1 there is nothing to connect.
    if not closes or len(closes) < 2:
        return None

    min_price = min(closes)
    max_price = max(closes)
    price_range = max_price - min_price

    # A flat-line stock (no movement at all) would divide by zero below.
    # Fall back to 1 so it draws as a flat horizontal line instead of crashing.
    if price_range == 0:
        price_range = 1

    # The area the line is actually allowed to occupy, after removing the margin.
    draw_width = width - 2 * padding
    draw_height = height - 2 * padding

    n = len(closes)
    points = []
    
    for i, price in enumerate(closes):
        # x: spread points evenly left-to-right inside the drawable area
        x = padding + (i / (n - 1)) * draw_width

        # y: SVG's y-axis grows DOWNWARD (0 = top), opposite of price intuition.
        # Invert so the highest price lands near the top, the lowest near the bottom.
        y = padding + draw_height - ((price - min_price) / price_range) * draw_height

        points.append(f"{x:.1f},{y:.1f}")


    # SVG wants one string of "x,y x,y x,y" pairs separated by spaces
    return " ".join(points)