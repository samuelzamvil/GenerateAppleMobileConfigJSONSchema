
import yaml
import json
import re

# Load YAML content
with open("com.apple.applicationaccess.yaml", 'r') as file:
    yaml_content = yaml.safe_load(file)

# Updated functions to incorporate today's changes

def convert_yaml_to_json_schema(yaml_data):
    properties = {}
    for entry in yaml_data['payloadkeys']:
        prop = {}
        key_name = entry['key']
        
        # Check for 'type'
        if "type" in entry:
            type_value = entry["type"]
            if type_value.startswith("<") and type_value.endswith(">"):
                type_value = type_value[1:-1]  # Remove angle brackets
            if type_value == "string":
                prop["type"] = "string"
            elif type_value == "boolean":
                prop["type"] = "boolean"
            elif type_value == "real":
                prop["type"] = "number"
            elif type_value == "integer":
                prop["type"] = "integer"
            elif type_value == "array":
                prop["type"] = "array"
            prop["anyOf"] = [{"type": "null", "title": "Not Configured"},
                             {"title": "Configured", "type": prop["type"]}]
        
        # Check for 'default' value
        if "default" in entry:
            prop["default"] = entry["default"]
            if "anyOf" in prop:
                for item in prop["anyOf"]:
                    if item.get("title") == "Configured":
                        item["default"] = prop["default"]

                        # Check for 'range' value
                        if "range" in entry:
                            min_value = entry["range"].get("min", "")
                            max_value = entry["range"].get("max", "")
                            if min_value and max_value:
                                item["pattern"] = f"[{min_value}-{max_value}]"

                        # Check for 'rangelist' value
                        if "rangelist" in entry:
                            item["enum"] = entry["rangelist"]

        # Add 'description' if available
        if "content" in entry:
            prop["description"] = entry["content"]

        properties[key_name] = prop

    return properties

def refine_properties_for_os_with_filter(properties, os_type):
    refined_properties = {}
    
    for key, value in properties.items():
        entry = next((item for item in yaml_content['payloadkeys'] if item["key"] == key), None)
        
        if not entry:
            continue

        if "supportedOS" not in entry:  # Universal key
            refined_properties[key] = value
            continue

        if os_type in entry["supportedOS"]:
            # If 'introduced' is 'n/a', continue to the next property
            if entry["supportedOS"][os_type].get("introduced") == "n/a":
                continue

            # Include all data under ['supportedOS'][osVersion] in the '_comment' key
            os_data = entry["supportedOS"][os_type]
            value["_comment"] = json.dumps(os_data)
            refined_properties[key] = value

        # Apply the same logic for subkeys if they exist
        if "properties" in value:
            refined_subkeys = refine_properties_for_os_with_filter_updated(value["properties"], os_type)
            if refined_subkeys:
                value["properties"] = refined_subkeys
                refined_properties[key] = value

    return refined_properties


def encapsulate_json(schema, yaml_data):
    encapsulated_schema = {
        "title": yaml_data["title"],
        "description": yaml_data["description"],
        "__preferencedomain": yaml_data["payload"]["payloadtype"],
        "properties": schema["properties"]
    }
    return encapsulated_schema

# Generating the third (final) portion of the code for review


# Extract the properties
json_schema_properties = convert_yaml_to_json_schema(yaml_content)

# Refine properties for each OS
macOS_properties_refined = refine_properties_for_os_with_filter(json_schema_properties, "macOS")
iOS_properties_refined = refine_properties_for_os_with_filter(json_schema_properties, "iOS")
tvOS_properties_refined = refine_properties_for_os_with_filter(json_schema_properties, "tvOS")

# Encapsulate the properties
macOS_schema = encapsulate_json({"properties": macOS_properties_refined}, yaml_content)
iOS_schema = encapsulate_json({"properties": iOS_properties_refined}, yaml_content)
tvOS_schema = encapsulate_json({"properties": tvOS_properties_refined}, yaml_content)

# File paths for saving the JSON schemas
macOS_file_path = "GeneratedFiles/macOS_schema.json"
iOS_file_path = "GeneratedFiles/iOS_schema.json"
tvOS_file_path = "GeneratedFiles/tvOS_schema.json"

# Save the schemas to files
with open(macOS_file_path, "w") as json_file:
    json.dump(macOS_schema, json_file, indent=4)
with open(iOS_file_path, "w") as json_file:
    json.dump(iOS_schema, json_file, indent=4)
with open(tvOS_file_path, "w") as json_file:
    json.dump(tvOS_schema, json_file, indent=4)

macOS_file_path, iOS_file_path, tvOS_file_path