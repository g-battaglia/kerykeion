from re import sub
import jsonpickle
import json

from kerykeion import KrInstance
from pathlib import Path


def dangerous_json_dump(subject: KrInstance, dump=True, new_output_directory=None):
    """
        Dumps the Kerykeion object to a json file located in the home folder.
        This json file allows the object to be recreated with jsonpickle.
        It's dangerous since it contains local system information.
        """

    OUTPUT_DIR = Path.home()

    try:
        subject.sun
    except:
        subject.__get_all()

    if new_output_directory:
        output_directory_path = Path(new_output_directory)
        json_dir = new_output_directory / \
            f"{subject.name}_kerykeion.json"
    else:
        json_dir = f"{subject.name}_kerykeion.json"

    json_string = jsonpickle.encode(subject)

    if dump:
        json_string = json.loads(json_string.replace(
            "'", '"'))  # type: ignore TODO: Fix this

        with open(json_dir, "w", encoding="utf-8") as file:
            json.dump(json_string, file,  indent=4, sort_keys=True)
            subject.__logger.info(f"JSON file dumped in {json_dir}.")
    else:
        pass
    return json_string
