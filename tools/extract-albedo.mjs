import { NodeIO } from '@gltf-transform/core';
import { KHRONOS_EXTENSIONS } from '@gltf-transform/extensions';
import { writeFileSync } from 'node:fs';
const io = new NodeIO().registerExtensions(KHRONOS_EXTENSIONS);
const doc = await io.read(process.argv[2]);
const tex = doc.getRoot().listTextures();
console.log('textures', tex.map(t => [t.getName(), t.getMimeType(), t.getImage()?.byteLength, t.getSize()]));
if (tex[0]) { const ext = tex[0].getMimeType().includes('png') ? 'png' : 'jpg'; writeFileSync(process.argv[3] + '.' + ext, Buffer.from(tex[0].getImage())); console.log('wrote', process.argv[3] + '.' + ext); }
const mats = doc.getRoot().listMaterials().map(m => ({ name: m.getName(), baseColor: m.getBaseColorFactor(), hasTex: !!m.getBaseColorTexture(), unlit: m.getExtension('KHR_materials_unlit') != null, rough: m.getRoughnessFactor(), metal: m.getMetallicFactor() }));
console.log(JSON.stringify(mats));
