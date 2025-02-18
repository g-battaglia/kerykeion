import re
from bs4 import BeautifulSoup, Tag
import cssutils
from typing import Dict


def extract_css_variables(svg_content: str) -> Dict[str, str]:
    """
    Extracts CSS variables from the <style> tag in an SVG file.

    :param svg_content: The raw SVG file content as a string.
    :return: A dictionary mapping CSS variable names to their values.
    """
    soup: BeautifulSoup = BeautifulSoup(svg_content, "xml")
    style_tag: Tag | None = soup.find("style")
    css_variables: Dict[str, str] = {}

    if style_tag:
        css = cssutils.parseString(style_tag.text)
        for rule in css:
            if rule.type == rule.STYLE_RULE:
                for property_name in rule.style:
                    if property_name.startswith("--"):  # Only capture CSS variables
                        css_variables[property_name] = rule.style[property_name]

    return css_variables


def replace_css_variables_with_inline_styles(svg_content: str) -> str:
    """
    Converts CSS variables to inline styles in an SVG file.

    :param svg_content: The raw SVG file content as a string.
    :return: The updated SVG content with inline styles.
    """
    soup: BeautifulSoup = BeautifulSoup(svg_content, "xml")
    css_variables: Dict[str, str] = extract_css_variables(svg_content)

    if not css_variables:
        return str(soup)  # No variables to replace, return as-is

    for element in soup.find_all(True):  # Iterate over all SVG elements
        if isinstance(element, Tag) and element.has_attr("style"):
            new_style: str = element["style"]
            for var, value in css_variables.items():
                var_pattern: str = f"var\\({re.escape(var)}\\)"
                new_style = re.sub(var_pattern, value, new_style)  # Replace CSS variable
            element["style"] = new_style  # Apply updated styles

    # Remove the <style> tag since it's no longer needed
    for style_tag in soup.find_all("style"):
        style_tag.decompose()

    return str(soup)
