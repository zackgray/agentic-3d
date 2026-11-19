"""Shared state for the checks: world-space bmeshes of the scene's mesh objects, built once each."""
import bmesh
import bpy


def world_bm(obj):
    bm = bmesh.new()
    bm.from_object(obj, bpy.context.evaluated_depsgraph_get())
    bm.transform(obj.matrix_world)
    for seq in (bm.verts, bm.edges, bm.faces):
        seq.ensure_lookup_table()
    return bm


def mm(v):
    return round(v * 1000, 3)


class Scene:
    def __init__(self):
        self._bm = {}

    def obj(self, name):
        o = bpy.data.objects.get(name)
        return o if o is not None and o.type == "MESH" else None

    def mesh_names(self):
        return sorted(o.name for o in bpy.context.scene.objects if o.type == "MESH")

    def bm(self, name):
        if name not in self._bm:
            self._bm[name] = world_bm(self.obj(name))
        return self._bm[name]
