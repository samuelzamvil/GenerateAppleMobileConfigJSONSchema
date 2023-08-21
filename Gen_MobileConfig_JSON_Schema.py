
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
            prop["type"] = convert_type(entry["type"])
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

            # Include all data under ['supportedOS'][osVersion] in the 'description' key
            os_data = entry["supportedOS"][os_type]
            value["description"] += f"\n{json.dumps(os_data)}"
            refined_properties[key] = value
            # Apply the same logic for subkeys if they exist
            if entry.get("subkeys"):
                for subkey in entry["subkeys"]:
                    key_name = subkey["key"]
                    type = convert_type(subkey["type"])
                    description = subkey["title"]
                    properties[key]["anyOf"][-1][key_name] = {"type": type, "description": description}

    return refined_properties

preference_domain = yaml_content["payload"]["payloadtype"]

def encapsulate_json(schema, yaml_data):
    encapsulated_schema = {
        "title": yaml_data["title"],
        "description": yaml_data["description"],
        "__preferencedomain": yaml_data["payload"]["payloadtype"],
        "properties": schema["properties"]
    }
    return encapsulated_schema


def convert_type(type_value):
        if type_value.startswith("<") and type_value.endswith(">"):
            type_value = type_value[1:-1]  # Remove angle brackets
        if type_value == "string":
            return "string"
        elif type_value == "boolean":
            return "boolean"
        elif type_value == "real":
            return "number"
        elif type_value == "integer":
            return "integer"
        elif type_value == "array":
            return "array"
        


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
macOS_file_path = f"{preference_domain}/{preference_domain}.macOS.schema.json"
iOS_file_path = f"{preference_domain}/{preference_domain}.iOS.schema.json"
tvOS_file_path = f"{preference_domain}/{preference_domain}.tvOS.schema.json"

# Save the schemas to files
with open(macOS_file_path, "w") as json_file:
    json.dump(macOS_schema, json_file, indent=4)
with open(iOS_file_path, "w") as json_file:
    json.dump(iOS_schema, json_file, indent=4)
with open(tvOS_file_path, "w") as json_file:
    json.dump(tvOS_schema, json_file, indent=4)

macOS_file_path, iOS_file_path, tvOS_file_path
