import json

config = {
    "mod_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DoorKickers2\\mods",
    "game_path": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\DoorKickers2",
    "last_used_mod": "baby_seals_with_custom_deploy_ui"
}

with open('modding_tool_config.json', 'w') as f:
    json.dump(config, f, indent=4) 