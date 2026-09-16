// Runtime model = geometry + UVs only; the albedo lives in the four baked passes.
// Input must be uncompressed (tools/coral-res.glb). Draco is applied afterwards by the CLI.
import { NodeIO } from '@gltf-transform/core';
import { KHRONOS_EXTENSIONS } from '@gltf-transform/extensions';
import { prune } from '@gltf-transform/functions';
const io = new NodeIO().registerExtensions(KHRONOS_EXTENSIONS);
const doc = await io.read(process.argv[2]);
let verts = 0, tris = 0;
for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) {
  verts += prim.getAttribute('POSITION').getCount();
  tris += (prim.getIndices() ? prim.getIndices().getCount() : prim.getAttribute('POSITION').getCount()) / 3;
  const mat = prim.getMaterial();
  if (mat) { mat.setBaseColorTexture(null); mat.setMetallicRoughnessTexture(null); mat.setNormalTexture(null); mat.setOcclusionTexture(null); mat.setEmissiveTexture(null); }
}
await doc.transform(prune({ keepAttributes: true, keepLeaves: true, keepIndices: true }));
await io.write(process.argv[3], doc);
console.log(JSON.stringify({ verts, tris, textures: doc.getRoot().listTextures().length }));
