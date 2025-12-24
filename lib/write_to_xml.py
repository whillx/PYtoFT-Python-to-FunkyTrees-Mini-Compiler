from pathlib import Path
import re

def insert_variables_text(xml_path: str, variables_content: str, path_checked: bool = True) -> None:
    """
    Insert or replace content inside a <Variables> block
    based on the presence of a <Variables /> tag.
    """

    xml_file = Path(xml_path)

    if not path_checked:
        if not xml_file.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")

    text = xml_file.read_text(encoding="utf-8")

    # Locate first <Assembly> tag
    assembly_match = re.search(r"<Assembly>", text)
    if not assembly_match:
        raise ValueError("No <Assembly> tag found in the XML file.")
    # locate first self-closing <Variables /> tag before <Assembly>
    variables_self_closing_match = re.search(r"<Variables />", text[:assembly_match.start()]) 
    if variables_self_closing_match:
        insert_start_pos = variables_self_closing_match.start()
    else:
        insert_start_pos = assembly_match.start()
    insert_end_pos = assembly_match.start()
    
    # Look for a <Variables> block <Assembly>
    variables_block_pattern = re.compile(
        r"<Variables>(.*?)</Variables>",
        re.DOTALL
    )

    existing_block_match = None
    for match in variables_block_pattern.finditer(text):
        if match.start() < insert_start_pos:
            existing_block_match = match
            break

    if existing_block_match:
        # Replace content inside existing <Variables> block
        new_block = (
            "<Variables>\n"
            f"{variables_content}\n"
            "  </Variables>"
        )

        text = (
            text[:existing_block_match.start()]
            + new_block
            + text[existing_block_match.end():]
        )

    else:
        # Insert new <Variables> block above <Assembly>
        new_block = (
            "<Variables>\n"
            f"{variables_content}\n"
            "  </Variables>\n  "
        )

        text = text[:insert_start_pos] + new_block + text[insert_end_pos:]

    # Write back to file
    xml_file.write_text(text, encoding="utf-8")


# -------------------------
# Example usage
# -------------------------

if __name__ == "__main__":
    xml_path = r"C:\path\to\your\file.xml"

    variables_text = """
    <Var name="Speed" value="10"/>
    <Var name="Power" value="5"/>
    """

    insert_variables_text(xml_path, variables_text)
