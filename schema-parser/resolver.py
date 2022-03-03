import singer
import json
import os

#list of files to transform
file_names = []
for file in  os.listdir("."):
    if file.endswith(".json"):
        file_names.append(file)

for schema_file in file_names:
    with open(schema_file) as f:
        old_schema = json.load(f)
        new_schema = singer.resolve_schema_references(old_schema)
        with open(f"./parsed_schemas/{schema_file}", "w") as w:
            w.write(json.dumps(new_schema, indent=4))


