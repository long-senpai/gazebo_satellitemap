"""
Export Web-Mercator XYZ tiles (PNG) from a local GeoTIFF for the Gazebo ortho pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, List, Optional

import cv2
import mercantile
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import Window

from utils.fileWriter import FileWriter
from utils.param import globalParam


def safe_tiff_path(filename: str) -> Path:
    base = Path(globalParam.TIFF_IMG_PATH).resolve()
    if ".." in filename or filename.startswith("/"):
        raise ValueError("Invalid GeoTIFF filename")
    candidate = (base / filename).resolve()
    if not str(candidate).startswith(str(base)):
        raise ValueError("Invalid GeoTIFF path")
    if candidate.suffix.lower() not in (".tif", ".tiff"):
        raise ValueError("File must be .tif or .tiff")
    if not candidate.is_file():
        raise ValueError(f"GeoTIFF not found: {filename}")
    return candidate


def list_geotiffs() -> List[dict]:
    base = Path(globalParam.TIFF_IMG_PATH)
    out: List[dict] = []
    if not base.is_dir():
        return out
    for p in sorted(base.glob("*.tif")):
        try:
            with rasterio.open(p) as src:
                w, s, e, n = transform_bounds(
                    src.crs, "EPSG:4326", *src.bounds, densify_pts=21
                )
                crs_s = src.crs.to_string() if src.crs else ""
                bands = src.count
            out.append(
                {
                    "filename": p.name,
                    "west": w,
                    "south": s,
                    "east": e,
                    "north": n,
                    "crs": crs_s,
                    "bands": bands,
                }
            )
        except Exception as exc:
            out.append({"filename": p.name, "error": str(exc)})
    return out


def _to_uint8_rgb(data: np.ndarray) -> np.ndarray:
    """data shape (3, h, w)."""
    if data.dtype == np.uint8:
        return data
    d = np.clip(data.astype(np.float32), 0, None)
    p99 = float(np.percentile(d, 99.5))
    if p99 < 1.0:
        p99 = max(float(d.max()), 1.0)
    d = np.clip(d / p99 * 255.0, 0, 255).astype(np.uint8)
    return d


def export_one_tile(
    src_path: str,
    tile: mercantile.Tile,
    out_png: str,
    tile_size: int = 256,
) -> None:
    left, bottom, right, top = mercantile.xy_bounds(tile)
    dst_transform = from_bounds(left, bottom, right, top, tile_size, tile_size)
    tb = mercantile.bounds(tile)
    west, south, east, north = tb.west, tb.south, tb.east, tb.north

    with rasterio.open(src_path) as src:
        src_left, src_bottom, src_right, src_top = transform_bounds(
            "EPSG:4326", src.crs, west, south, east, north, densify_pts=21
        )
        win = rasterio.windows.from_bounds(
            src_left, src_bottom, src_right, src_top, transform=src.transform
        )
        win = win.round_offsets().intersection(Window(0, 0, src.width, src.height))

        if win.width < 1 or win.height < 1:
            blank = np.zeros((tile_size, tile_size, 3), dtype=np.uint8)
            os.makedirs(os.path.dirname(out_png), exist_ok=True)
            cv2.imwrite(out_png, blank)
            return

        if src.count >= 3:
            bands = (1, 2, 3)
        else:
            bands = (1,)
        data = src.read(bands, window=win, boundless=True, fill_value=0)
        if data.shape[0] == 1:
            data = np.concatenate([data, data, data], axis=0)
        data = _to_uint8_rgb(data)
        transform_win = src.window_transform(win)

        dst = np.zeros((3, tile_size, tile_size), dtype=np.uint8)
        reproject(
            source=data,
            destination=dst,
            src_transform=transform_win,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs="EPSG:3857",
            resampling=Resampling.bilinear,
        )
        rgb = np.moveaxis(dst, 0, -1)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        os.makedirs(os.path.dirname(out_png), exist_ok=True)
        cv2.imwrite(out_png, bgr)


def iter_tiles_wsen(west: float, south: float, east: float, north: float, zoom: int):
    return list(mercantile.tiles(west, south, east, north, zooms=zoom))


def export_geotiff_to_output(
    geotiff_filename: str,
    output_directory: str,
    zoom: int,
    bounds_wsen: List[float],
    lock,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> int:
    """
    Write tiles to OUTPUT_BASE_PATH/output_directory/z/x/y.png.
    bounds_wsen: [west, south, east, north] (WGS84), same convention as the web UI.
    Returns number of tiles written.
    """
    src_path = str(safe_tiff_path(geotiff_filename))
    west, south, east, north = bounds_wsen
    tiles = iter_tiles_wsen(west, south, east, north, zoom)
    total = len(tiles)
    base_out = os.path.join(globalParam.OUTPUT_BASE_PATH, output_directory, str(zoom))

    for i, tile in enumerate(tiles):
        out_dir = os.path.join(base_out, str(tile.x))
        FileWriter.ensureDirectory(lock, out_dir)
        out_png = os.path.join(out_dir, f"{tile.y}.png")
        export_one_tile(src_path, tile, out_png)
        if progress_cb and (i % max(1, total // 50) == 0 or i == total - 1):
            progress_cb(i + 1, total)
    return total
