import json


def convert_theme_to_new_theme(theme: dict) -> dict:
    return {
        "categories": theme["categories"],
        "displayName": theme["displayName"],
        "publisher": {
            "displayName": theme["publisher.displayName"],
            "publisherName": theme["publisher.publisherName"],
        },
        "tags": theme["tags"],
        "extension": {
            "extensionId": theme["extension.extensionId"],
            "extensionName": theme["extension.extensionName"],
            "latestVersion": theme["extension.latestVersion"],
            "downloadUrl": theme["extension.downloadUrl"],
        },
        "theme_files": theme["theme_files"],
        "vsix_path": theme["vsix_path"],
        "theme_dir": theme["theme_dir"],
    }


def convert_json(input_file: str, output_file: str):
    with open(input_file, "r") as f:
        themes = json.load(f)

    new_themes = [convert_theme_to_new_theme(theme) for theme in themes]

    with open(output_file, "w") as f:
        json.dump(new_themes, f, indent=4)


# Example usage
input_file = "themes/list.json"
output_file = "new_themes.json"
convert_json(input_file, output_file)
