# Gazebo Satellite Map

A straightforward tool to build 3D Gazebo worlds from real-world elevation and satellite imagery for any area on Earth.

<p align="center">
  <img src="gif/thumnail.png" alt="Web UI — region selection" width="1050"/>
</p>

<p align="center">
  <img src="gif/building.png" alt="3D terrain with buildings in Gazebo" width="1050"/>
</p>

## Features

- **Real-world terrain**: Worlds use elevation data and satellite tiles for the area you choose.
- **3D buildings**: Optional buildings in the generated world (toggle in the UI).
- **Spawn location**: Set spawn via the interactive marker inside your region.
- **Configurable output**: Model and world paths via environment variables.
- **Resolution**: Adjustable map zoom / tile resolution.
- **End-to-end workflow**: Web UI → download tiles → heightmap + texture → Gazebo model/world.

## Supported stack

- **[Gazebo Harmonic](https://gazebosim.org/docs/harmonic/install_ubuntu/)**

## Setup

### Virtual environment (recommended)

```bash
python3 -m venv terrain_generator
source terrain_generator/bin/activate
```

### Dependencies

With the venv active:

```bash
pip install -r requirements.txt
```

## Configuration

### Environment variables

```bash
export GAZEBO_MODEL_PATH="~/Desktop/gazebo_models"
export GAZEBO_WORLD_PATH="~/Desktop/gazebo_models/worlds"
```

**Defaults** (if unset, see [`scripts/utils/param.py`](scripts/utils/param.py)): models go to `output/gazebo_terrain/` and worlds to `output/gazebo_terrain/worlds/`, relative to the project root (the folder that contains `scripts/`).

### Generated layout

```
<GAZEBO_MODEL_PATH>/
├── model_name/
│   ├── model.sdf
│   ├── model.config
│   ├── model_name.sdf
│   └── textures/
│       ├── world_name_height_map.tif
│       └── world_name_aerial.png
<GAZEBO_WORLD_PATH>/
├── model_name.sdf
├── model_name_1.sdf
└── ...
```

## Run the generator

1. From this directory (where `scripts/` lives), with venv active:

   ```bash
   python scripts/server.py
   ```

2. Open **http://localhost:8080** in a browser.

3. In the UI:
   - Search by place name **or** enter latitude / longitude.
   - Draw a rectangular region.
   - Move the launch marker to the desired spawn point.
   - Toggle buildings if needed.
   - Set zoom level and map tile source.
   - Click **Generate Terrain** (or equivalent) to build the world.

4. Outputs go to the paths you configured (see above).

## Run worlds in Gazebo

1. **Resource path** (Harmonic / `gz sim`):

   ```bash
   export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:<path_to_models_parent>
   ```

2. **Launch**:

   ```bash
   gz sim your_world/your_world.sdf
   ```

Replace `<path_to_models_parent>` with the folder that contains your model packages (often the same as `GAZEBO_MODEL_PATH` or its parent, depending on how you export).

## Sample worlds

If this repo includes `sample_worlds`:

```bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$(pwd)/sample_worlds
gz sim prayag/prayag.sdf
```

## Mapbox token

The UI uses Mapbox for the map. If the bundled token hits rate limits, create a key at [mapbox.com](https://www.mapbox.com/) and set it in [`scripts/utils/param.py`](scripts/utils/param.py) (or wherever your build keeps the token).

## Disclaimer

Downloading tiles is subject to each provider’s terms of use. Some sources (e.g. Google, Bing, ESRI) restrict automated or bulk download; do not use them commercially without permission.

## License

This project is under the **BSD 3-Clause License** — see [LICENSE](LICENSE).

Portions derive from **MapTilesDownloader** by [Ali Ashraf](https://github.com/AliFlux/MapTilesDownloader), licensed under the **MIT License**; those parts stay under MIT.

## References

- [Creating heightmaps for Gazebo](https://github.com/AS4SR/general_info/wiki/Creating-Heightmaps-for-Gazebo)
- [Mapbox Terrain-DEM v1](https://docs.mapbox.com/data/tilesets/reference/mapbox-terrain-dem-v1/)
