"""
🔍 GLB Model Inspector
Quick inspection tool for .glb files to check animations, morph targets, and structure
No Blender needed!

Usage: python inspect_glb.py assets/models/avatar.glb
"""

import sys
import json
from pathlib import Path

try:
    from pygltflib import GLTF2
except ImportError:
    print("❌ pygltflib not installed!")
    print("Install with: pip install pygltflib")
    sys.exit(1)


def inspect_glb(file_path):
    """Inspect a GLB file and print detailed information"""
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print("\n" + "="*60)
    print(f"🔍 INSPECTING: {Path(file_path).name}")
    print("="*60 + "\n")
    
    try:
        gltf = GLTF2().load(file_path)
        
        # === ANIMATIONS ===
        print("📹 ANIMATIONS")
        print("-" * 60)
        if gltf.animations:
            print(f"✅ Found {len(gltf.animations)} animation(s)\n")
            
            for i, anim in enumerate(gltf.animations):
                name = anim.name if anim.name else f"Animation_{i}"
                print(f"  [{i}] {name}")
                print(f"      Channels: {len(anim.channels)}")
                print(f"      Samplers: {len(anim.samplers)}")
                
                # Analyze what this animates
                if anim.channels:
                    target_paths = set()
                    for channel in anim.channels:
                        target_paths.add(channel.target.path)
                    
                    print(f"      Animates: {', '.join(target_paths)}")
                print()
        else:
            print("❌ No animations found\n")
        
        # === MESHES & MORPH TARGETS ===
        print("\n🎭 MESHES & MORPH TARGETS")
        print("-" * 60)
        if gltf.meshes:
            total_morphs = 0
            
            for i, mesh in enumerate(gltf.meshes):
                mesh_name = mesh.name if mesh.name else f"Mesh_{i}"
                print(f"\n  [{i}] {mesh_name}")
                print(f"      Primitives: {len(mesh.primitives)}")
                
                # Check for morph targets in each primitive
                for prim_idx, primitive in enumerate(mesh.primitives):
                    if hasattr(primitive, 'targets') and primitive.targets:
                        num_targets = len(primitive.targets)
                        total_morphs += num_targets
                        print(f"      Primitive {prim_idx}: {num_targets} morph targets")
                        
                        # Try to get target names from extras
                        if hasattr(primitive, 'extras') and primitive.extras:
                            try:
                                extras = json.loads(primitive.extras) if isinstance(primitive.extras, str) else primitive.extras
                                if 'targetNames' in extras:
                                    print(f"         Names: {', '.join(extras['targetNames'][:5])}...")
                            except:
                                pass
            
            print(f"\n  Total morph targets across all meshes: {total_morphs}")
        else:
            print("❌ No meshes found")
        
        # === NODES ===
        print("\n\n🌳 SCENE STRUCTURE")
        print("-" * 60)
        if gltf.nodes:
            print(f"Total nodes: {len(gltf.nodes)}\n")
            
            # Find root nodes (nodes not referenced by other nodes)
            all_children = set()
            for node in gltf.nodes:
                if hasattr(node, 'children') and node.children:
                    all_children.update(node.children)
            
            root_indices = [i for i in range(len(gltf.nodes)) if i not in all_children]
            
            def print_node_tree(node_idx, depth=0):
                if node_idx >= len(gltf.nodes):
                    return
                    
                node = gltf.nodes[node_idx]
                name = node.name if node.name else f"Node_{node_idx}"
                indent = "  " * depth
                
                info = []
                if hasattr(node, 'mesh') and node.mesh is not None:
                    info.append(f"mesh={node.mesh}")
                if hasattr(node, 'skin') and node.skin is not None:
                    info.append("skinned")
                
                info_str = f" ({', '.join(info)})" if info else ""
                print(f"{indent}├─ {name}{info_str}")
                
                if hasattr(node, 'children') and node.children:
                    for child_idx in node.children[:3]:  # Limit to first 3 children
                        print_node_tree(child_idx, depth + 1)
                    if len(node.children) > 3:
                        print(f"{indent}   └─ ... ({len(node.children) - 3} more)")
            
            print("Root nodes:")
            for root_idx in root_indices[:5]:  # Show first 5 roots
                print_node_tree(root_idx)
            
            if len(root_indices) > 5:
                print(f"  ... ({len(root_indices) - 5} more root nodes)")
        
        # === SKINS (Rigging) ===
        print("\n\n🦴 RIGGING")
        print("-" * 60)
        if gltf.skins:
            print(f"✅ Found {len(gltf.skins)} skin(s)")
            for i, skin in enumerate(gltf.skins):
                name = skin.name if skin.name else f"Skin_{i}"
                print(f"  [{i}] {name}")
                print(f"      Joints: {len(skin.joints)}")
        else:
            print("❌ No skins/rigging found")
        
        # === SUMMARY ===
        print("\n\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"Animations:    {len(gltf.animations) if gltf.animations else 0}")
        print(f"Meshes:        {len(gltf.meshes) if gltf.meshes else 0}")
        print(f"Nodes:         {len(gltf.nodes) if gltf.nodes else 0}")
        print(f"Skins:         {len(gltf.skins) if gltf.skins else 0}")
        print(f"Textures:      {len(gltf.textures) if gltf.textures else 0}")
        print(f"Materials:     {len(gltf.materials) if gltf.materials else 0}")
        
        # File size
        file_size = Path(file_path).stat().st_size
        size_mb = file_size / (1024 * 1024)
        print(f"File size:     {size_mb:.2f} MB")
        
        print("\n✅ Inspection complete!\n")
        
    except Exception as e:
        print(f"\n❌ Error inspecting file: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n🔍 GLB Inspector Tool")
        print("\nUsage: python inspect_glb.py <path_to_glb_file>")
        print("\nExample:")
        print("  python inspect_glb.py assets/models/avatar.glb")
        print()
        sys.exit(1)
    
    file_path = sys.argv[1]
    inspect_glb(file_path)