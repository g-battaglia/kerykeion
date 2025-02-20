import re

import logging

from typing import Dict

# Suppress cssutils warnings


def resolve_nested_variables(value: str, css_variables: Dict[str, str]) -> str:
    """
    Recursively replaces var(--something) with its actual value from CSS variables.
    """
    while "var(--" in value:  # Keep resolving until no nested variables remain
        match = re.search(r"var\((--[^)]+)\)", value)
        if not match:
            break
        var_name = match.group(1)  # Extract --variable-name
        replacement = css_variables.get(var_name, match.group(0))  # Replace if exists
        value = value.replace(match.group(0), replacement)
    return value

def extract_css_variables(svg_content: str) -> Dict[str, str]:
    """
    Extracts all CSS variables from <style> blocks in the SVG.
    """
    import cssutils
    cssutils.log.setLevel(logging.CRITICAL)
    soup: BeautifulSoup = BeautifulSoup(svg_content, "xml")
    css_variables: Dict[str, str] = {}

    for style_tag in soup.find_all("style"):
        css = cssutils.parseString(style_tag.text)
        for rule in css:
            if rule.type == rule.STYLE_RULE:
                for i in range(rule.style.length):
                    property_name: str = rule.style.item(i)
                    if property_name.startswith("--"):  # Only capture CSS variables
                        css_variables[property_name] = resolve_nested_variables(
                            rule.style.getPropertyValue(property_name), css_variables
                        )  # Resolve if nested variables exist

    return css_variables

def replace_css_variables(svg_content: str) -> str:
    """
    Converts CSS variables to inline styles and direct attributes in an SVG file.
    """
    from bs4 import BeautifulSoup, Tag
    soup: BeautifulSoup = BeautifulSoup(svg_content, "xml")
    css_variables: Dict[str, str] = extract_css_variables(svg_content)

    if not css_variables:
        return str(soup)  # No variables found, return unchanged SVG

    # Process elements with style attributes
    for element in soup.find_all(True):  # Iterate over all SVG elements
        if isinstance(element, Tag):
            # Replace CSS variables in style=""
            if element.has_attr("style"):
                new_style: str = element["style"]
                for var, value in css_variables.items():
                    var_pattern: str = f"var\\({re.escape(var)}\\)"
                    new_style = re.sub(var_pattern, value, new_style)  # Replace CSS variable
                element["style"] = new_style  # Apply updated styles

            # Replace CSS variables in direct attributes like fill, stroke, etc.
            for attr in ["fill", "stroke", "stop-color"]:  # Add more attributes if needed
                if element.has_attr(attr):
                    attr_value = element[attr]
                    element[attr] = resolve_nested_variables(attr_value, css_variables)

    # Remove all <style> tags since they are no longer needed
    for style_tag in soup.find_all("style"):
        style_tag.decompose()

    return str(soup)
