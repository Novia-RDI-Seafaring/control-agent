from control_toolbox.tools.information import get_fmu_names, get_model_description, get_all_model_descriptions
from pathlib import Path

FMU_DIR = Path("models/fmus")


########################################################
# INFORMATION TOOLS
########################################################
# get model names
model_names = get_fmu_names(FMU_DIR)
print(80*"=")
print("Model Names:")
print(model_names.model_dump_json(indent=2))
print(80*"=")

# get model description
model_description = get_model_description(FMU_DIR, model_names.payload[0])
print(80*"=")
print("Model Description:")
print(model_description.model_dump_json(indent=2))
print(80*"=")

# get all model descriptions
all_model_descriptions = get_all_model_descriptions(FMU_DIR)
print(80*"=")
print("All Model Descriptions:")
print(all_model_descriptions.model_dump_json(indent=2))
print(80*"=")

