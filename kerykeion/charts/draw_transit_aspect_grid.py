def draw_transit_aspect_grid(
        stroke_color: str, 
        available_planets: list, 
        aspects: list,
        x_start: int = 50,
        y_start: int = 250
    ) -> str:
    """
    Draws the aspect grid for the given planets and aspects.

    Args:
        stroke_color (str): The color of the stroke.
        available_planets (list): List of all planets. Only planets with "is_active" set to True will be used.
        aspects (list): List of aspects.
        x_start (int): The x-coordinate starting point.
        y_start (int): The y-coordinate starting point.

    Returns:
        str: SVG string representing the aspect grid.
    """
    svg_output = ""
    style = f"stroke:{stroke_color}; stroke-width: 1px; stroke-opacity:.6; fill:none"
    box_size = 14

    # Filter active planets
    active_planets = [planet for planet in available_planets if planet.is_active]

    # Reverse the list of active planets for the first iteration
    reversed_planets = active_planets[::-1]
    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_a["name"]}" />'
        x_start += box_size

    x_start = 50 - box_size
    y_start = 250 - box_size

    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_a["name"]}" />'
        y_start -= box_size

    x_start = 50
    y_start = 250
    y_start = y_start - box_size

    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'

        # Update the starting coordinates for the next box
        y_start -= box_size

        # Coordinates for the aspect symbols
        x_aspect = x_start
        y_aspect = y_start + box_size

        # Iterate over the remaining planets
        for planet_b in reversed_planets:
            # Draw the grid box for the aspect
            svg_output += f'<rect x="{x_aspect}" y="{y_aspect}" width="{box_size}" height="{box_size}" style="{style}"/>'
            x_aspect += box_size

            # Check for aspects between the planets
            for aspect in aspects:
                if (aspect["p1"] == planet_a["id"] and aspect["p2"] == planet_b["id"]):
                    svg_output += f'<use  x="{x_aspect - box_size + 1}" y="{y_aspect + 1}" xlink:href="#orb{aspect["aspect_degrees"]}" />'
                    aspects.remove(aspect)

    return svg_output