import json

from ark.export_wiki.geo import GeoData
from ue.base import UEBase


def get_blueprint_path(obj):
    return f'{str(obj.namespace.value.name)}.{str(obj.name).rstrip("_C")}'


def unpack_defaultdict_value(obj):
    return obj[0] if obj else None


def export_properties_from_proxy(proxy, target_keys):
    return {target_keys[key]: unpack_defaultdict_value(getattr(proxy, key, None)) for key in target_keys.keys()}

def format_location_for_export(ue_coords: tuple, lat: GeoData, long: GeoData):
    if len(ue_coords) is 2:
        # XY pair
        return {"lat": lat.from_units(ue_coords[1]), "long": long.from_units(ue_coords[0])}

    if len(ue_coords) is 3:
        # XYZ pair, common for resources
        return {
            "x": ue_coords[0],
            "y": ue_coords[1],
            "z": ue_coords[2],
            "lat": lat.from_units(ue_coords[1]),
            "long": long.from_units(ue_coords[0])
        }

    # min[XY]max[XY] flat pair
    long_start = long.from_units(ue_coords[0])
    lat_start = lat.from_units(ue_coords[1])
    long_end = long.from_units(ue_coords[2])
    lat_end = lat.from_units(ue_coords[3])
    return {
        "latStart": lat_start,
        "longStart": long_start,
        "latEnd": lat_end,
        "longEnd": long_end,
        "latCenter": (lat_end+lat_start) / 2,
        "longCenter": (long_end+long_start) / 2,
    }

def get_volume_worldspace_bounds(volume, include_altitude=False):
    brush_component = volume.properties.get_property("BrushComponent").value.value
    body_setup = brush_component.properties.get_property("BrushBodySetup").value.value
    agg_geom = body_setup.properties.get_property("AggGeom").values[0].value
    convex_elems = agg_geom.values[0]
    volume_location = brush_component.properties.get_property("RelativeLocation").values[0]
    volume_box = convex_elems.as_dict()["ElemBox"].values[0]
    if include_altitude:
        # min[XYZ]max[XYZ] format
        return (
            # Min
            volume_box.min.x.value + volume_location.x.value,
            volume_box.min.y.value + volume_location.y.value,
            volume_box.min.z.value + volume_location.z.value,
            # Max
            volume_box.max.x.value + volume_location.x.value,
            volume_box.max.y.value + volume_location.y.value,
            volume_box.max.z.value + volume_location.z.value)

    # min[XY]max[XY] format
    return (
        # Min
        volume_box.min.x.value + volume_location.x.value,
        volume_box.min.y.value + volume_location.y.value,
        # Max
        volume_box.max.x.value + volume_location.x.value,
        volume_box.max.y.value + volume_location.y.value)

def property_serializer(obj):
    if hasattr(obj, 'format_for_json'):
        return obj.format_for_json()

    if isinstance(obj, UEBase):
        return str(obj)

    return json._default_encoder.default(obj)


def struct_entries_array_to_dict(struct_entries):
    return {str(struct_entry.name): struct_entry.value for struct_entry in struct_entries}
