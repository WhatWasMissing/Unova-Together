"""Bounded static Nitro field-mesh decoder. mvq1303, GPL-3.0-or-later.

Unsupported transforms/commands fail closed rather than inventing geometry.
Format references: CTRMapV NSBMDModel/NSBMDJoint; melonDS GPU3D geometry commands.
"""
import struct
import math
from functools import lru_cache


def dictionary(data, offset):
    if offset < 0 or offset+8 > len(data): raise ValueError('Dictionary bounds')
    count=data[offset+1]; info=offset+struct.unpack_from('<H',data,offset+6)[0]
    stride,names=struct.unpack_from('<HH',data,info)
    if stride != 4 or info+4+count*stride>len(data) or info+names+count*16 > len(data): raise ValueError('Dictionary layout')
    return [(data[info+names+i*16:info+names+(i+1)*16].rstrip(b'\0').decode('latin1'),
             struct.unpack_from('<I',data,info+4+i*4)[0]) for i in range(count)]


def signed(value,bits):
    return (value & ((1<<bits)-1)) - (1<<bits) if value & (1<<(bits-1)) else value & ((1<<bits)-1)


def display_faces(data, scale):
    # Vertex positions and UV coordinates are retained together when clipping.
    counts={0:0,0x14:1,0x20:1,0x21:1,0x22:1,0x23:2,0x24:1,0x25:1,
            0x26:1,0x27:1,0x28:1,0x40:1,0x41:0}
    position=[0.,0.,0.];uv=[0.,0.];vertices=[];faces=[];mode=None;i=0
    while i<len(data):
        if i+4>len(data): raise ValueError('Truncated GX commands')
        commands=data[i:i+4];i+=4
        for command in commands:
            if command not in counts: raise ValueError(f'Unsupported GX command {command:#x}')
            n=counts[command]
            if i+n*4>len(data): raise ValueError('Truncated GX parameters')
            args=struct.unpack_from(f'<{n}I',data,i) if n else ();i+=n*4
            if command==0x14:
                if args[0]!=0: raise ValueError('Non-root vertex matrix')
            elif command==0x22:
                uv=[signed(args[0],16)/16,signed(args[0]>>16,16)/16]
            elif command==0x40: mode=args[0]&3;vertices=[]
            elif command==0x41: mode=None
            elif 0x23<=command<=0x28:
                v=args[0]
                if command==0x23: position=[signed(v,16)/4096,signed(v>>16,16)/4096,signed(args[1],16)/4096]
                elif command==0x24: position=[signed(v>>(10*j),10)/64 for j in range(3)]
                elif command in (0x25,0x26,0x27):
                    axes={0x25:(0,1),0x26:(0,2),0x27:(1,2)}[command]
                    for j,axis in enumerate(axes):position[axis]=signed(v>>(16*j),16)/4096
                else:position=[position[j]+signed(v>>(10*j),10)/4096 for j in range(3)]
                if mode is None: raise ValueError('Vertex outside primitive')
                vertices.append(tuple(p*scale for p in position)+tuple(uv))
                length=len(vertices)
                if mode==0 and length%3==0:faces.append(vertices[-3:])
                elif mode==1 and length%4==0:faces.append(vertices[-4:])
                elif mode==2 and length>=3:
                    faces.append([vertices[-3],vertices[-2],vertices[-1]] if length%2 else [vertices[-2],vertices[-3],vertices[-1]])
                elif mode==3 and length>=4 and length%2==0:faces.append([vertices[-4],vertices[-3],vertices[-1],vertices[-2]])
    return faces


def _pivot_rotation(form, signs, a, b):
    """Decode the compact Nitro rotation used by a BoneMatrix."""
    if form > 8:
        raise ValueError('Unsupported pivot rotation form')
    one = -1.0 if signs & 1 else 1.0
    c = -b if signs & 2 else b
    d = -a if signs & 4 else a
    forms = (
        ((one, 0, 0), (0, a, b), (0, c, d)),
        ((0, one, 0), (a, 0, b), (c, 0, d)),
        ((0, 0, one), (a, b, 0), (c, d, 0)),
        ((0, a, b), (one, 0, 0), (0, c, d)),
        ((a, 0, b), (0, one, 0), (c, 0, d)),
        ((a, b, 0), (0, 0, one), (c, d, 0)),
        ((0, a, b), (0, c, d), (one, 0, 0)),
        ((a, 0, b), (c, 0, d), (0, one, 0)),
        ((a, b, 0), (c, d, 0), (0, 0, one)),
    )
    return forms[form]


def node_transform(data, offset):
    """Read one static NSBMD node as a row-major affine transform."""
    if offset < 0 or offset + 4 > len(data):
        raise ValueError('Node transform bounds')
    flags = struct.unpack_from('<H', data, offset)[0]
    cursor = offset + 4  # flags and the aligned m0/pivot-form word
    translation = (0.0, 0.0, 0.0)
    scales = (1.0, 1.0, 1.0)
    identity = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    rotation = identity
    if not flags & 1:
        translation = tuple(v / 4096.0 for v in struct.unpack_from('<3i', data, cursor))
        cursor += 12
    pivot = (flags >> 3) & 1
    matrix_rotation = (flags >> 1) & 1
    if pivot:
        form = (flags >> 4) & 0xF
        signs = (flags >> 8) & 0x7
        a, b = (v / 4096.0 for v in struct.unpack_from('<2h', data, cursor))
        cursor += 4
        rotation = _pivot_rotation(form, signs, a, b)
    elif not matrix_rotation:
        first = struct.unpack_from('<h', data, offset + 2)[0] / 4096.0
        rest = [v / 4096.0 for v in struct.unpack_from('<8h', data, cursor)]
        cursor += 16
        values = [first] + rest
        rotation = tuple(tuple(values[col * 3 + row] for col in range(3)) for row in range(3))
    if not flags & 4:
        scales = tuple(v / 4096.0 for v in struct.unpack_from('<3i', data, cursor))
    return tuple(tuple(rotation[row][col] * scales[col] for col in range(3)) + (translation[row],)
                 for row in range(3))


def _identity_affine():
    return ((1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0))


def _multiply_affine(left, right):
    """Compose two row-major 3x4 affine transforms (left * right)."""
    return tuple(tuple(
        sum(left[row][k] * right[k][col] for k in range(3))
        if col < 3 else
        sum(left[row][k] * right[k][3] for k in range(3)) + left[row][3]
        for col in range(4)) for row in range(3))


def _transform_face(face, matrix):
    return [tuple(sum(matrix[row][col] * vertex[col] for col in range(3)) + matrix[row][3]
                  for row in range(3)) + vertex[3:] for vertex in face]


def _crossed_billboard(face, matrix):
    """Add a second vertical plane for camera-facing field billboards."""
    origin = tuple(matrix[row][3] for row in range(3))
    result = []
    for vertex in face:
        x, y, z = vertex[:3]
        result.append((z - origin[2] + origin[0], y,
                       origin[2] - (x - origin[0])) + vertex[3:])
    return result


def _render_commands(data, nodes, meshes, pairs):
    """Interpret the static subset of Nitro's model render command stream."""
    matrix = _identity_affine()
    stack = [None] * 31
    material = None
    active_node = 0
    visible = True
    billboard_nodes = set()
    result = []
    at = 0

    def take(count, label):
        nonlocal at
        if at + count > len(data):
            raise ValueError(f'Truncated {label}')
        values = data[at:at + count]
        at += count
        return values

    def stack_index(value):
        if value >= len(stack):
            raise ValueError('SBC matrix stack index')
        return value

    while at < len(data):
        command = take(1, 'SBC')[0]
        op = command & 31
        flags = command >> 5
        if op == 0:
            continue
        if op == 1:
            break
        if op == 2:
            active_node, node_visible = take(2, 'SBC node')
            if active_node >= len(nodes):
                raise ValueError('SBC node index')
            visible = bool(node_visible & 1)
        elif op == 3:
            slot = stack_index(take(1, 'SBC matrix restore')[0])
            if stack[slot] is None:
                raise ValueError('SBC restored an unset matrix')
            matrix = stack[slot]
        elif op == 4:
            material = take(1, 'SBC material')[0]
        elif op == 5:
            mesh = take(1, 'SBC mesh')[0]
            if material is None or material >= len(pairs) or mesh >= len(meshes):
                raise ValueError('SBC mesh binding')
            if visible:
                for face in meshes[mesh]:
                    transformed = _transform_face(face, matrix)
                    result.append((tuple(pairs[material]), transformed))
                    if active_node in billboard_nodes:
                        result.append((tuple(pairs[material]), _crossed_billboard(transformed, matrix)))
        elif op == 6:
            args = take(3, 'SBC node transform')
            node = args[0]
            if node >= len(nodes):
                raise ValueError('SBC transformed node index')
            store_slot = stack_index(take(1, 'SBC node matrix store')[0]) if flags & 1 else None
            load_slot = stack_index(take(1, 'SBC node matrix load')[0]) if flags & 2 else None
            if load_slot is not None:
                if stack[load_slot] is None:
                    raise ValueError('SBC loaded an unset node matrix')
                matrix = stack[load_slot]
            matrix = _multiply_affine(matrix, nodes[node])
            if store_slot is not None:
                stack[store_slot] = matrix
        elif op in (7, 8):
            node = take(1, 'SBC billboard')[0]
            if node >= len(nodes):
                raise ValueError('SBC billboard node index')
            store_slot = stack_index(take(1, 'SBC billboard matrix store')[0]) if flags & 1 else None
            load_slot = stack_index(take(1, 'SBC billboard matrix load')[0]) if flags & 2 else None
            if load_slot is not None:
                if stack[load_slot] is None:
                    raise ValueError('SBC loaded an unset billboard matrix')
                matrix = stack[load_slot]
            billboard_nodes.add(node)
            if store_slot is not None:
                stack[store_slot] = matrix
        elif op in (11, 12, 13):
            # Position scaling is already applied to mesh vertices. Environment
            # and projection map commands affect texture coordinates only.
            take(0 if op == 11 else 2, 'SBC mapping')
        else:
            raise ValueError(f'Unsupported SBC {op}')
    if not result:
        raise ValueError('No field faces')
    return result


@lru_cache(maxsize=256)
def decode(data):
    if data[:4]!=b'BMD0' or len(data)<24: raise ValueError('Not a model')
    mdl=struct.unpack_from('<I',data,16)[0]
    models=dictionary(data,mdl+8)
    if len(models)!=1: raise ValueError('Multiple model resources')
    model=mdl+models[0][1]
    size,sbc_off,mat_off,mesh_off,_=struct.unpack_from('<5I',data,model)
    if model+size>len(data): raise ValueError('Model bounds')
    scale=struct.unpack_from('<i',data,model+28)[0]/4096
    # Field chunks store static local-to-parent node transforms. The SBC stream
    # supplies the hierarchy and matrix-stack operations needed to place meshes.
    nodes=dictionary(data,model+64)
    transforms=[node_transform(data,model+64+off) for _,off in nodes]
    base=model+mat_off;materials=dictionary(data,base+4)
    pairs=[['',''] for _ in materials]
    for j,off in enumerate(struct.unpack_from('<HH',data,base)):
        for name,value in dictionary(data,base+off):
            if value&0x1000000:continue
            start=base+(value&65535);count=(value>>16)&255
            if start+count>len(data):raise ValueError('Material binding bounds')
            for index in data[start:start+count]:
                if index>=len(pairs):raise ValueError('Material index')
                pairs[index][j]=name
    meshes=[]
    for _,off in dictionary(data,model+mesh_off):
        at=model+mesh_off+off
        _,_,dl,length=struct.unpack_from('<4I',data,at)
        if at+dl+length>len(data):raise ValueError('Mesh bounds')
        meshes.append(display_faces(data[at+dl:at+dl+length],scale))
    commands=data[model+sbc_off:model+mat_off]
    return _render_commands(commands,transforms,meshes,pairs)


def crop_face(vertices, radius):
    # Sutherland-Hodgman preserves source UVs at new intersection vertices.
    result=list(vertices)
    for axis in (0,2):
        for boundary,direction in ((-radius,1),(radius,-1)):
            source=result;result=[]
            if not source:break
            previous=source[-1];inside=(previous[axis]-boundary)*direction>=0
            for current in source:
                now=(current[axis]-boundary)*direction>=0
                if now != inside:
                    t=(boundary-previous[axis])/(current[axis]-previous[axis])
                    result.append(tuple(a+(b-a)*t for a,b in zip(previous,current)))
                if now:result.append(current)
                previous,inside=current,now
    return result


def polygon_overlaps_square(vertices, half_extent):
    """Return whether an X/Z polygon touches the protected battle centre.

    Faces are convex triangles or quads. Separating-axis checks include the
    square's edges and each polygon edge, so a long prop face crossing the
    centre is rejected even when every vertex lies outside the safe region.
    """
    if not math.isfinite(half_extent) or half_extent < 0:
        raise ValueError('Invalid protected-area extent')
    points=[(float(vertex[0]),float(vertex[2])) for vertex in vertices]
    if not points:
        return False
    if not all(math.isfinite(value) for point in points for value in point):
        raise ValueError('Non-finite polygon coordinate')
    square=[(-half_extent,-half_extent),(-half_extent,half_extent),
            (half_extent,half_extent),(half_extent,-half_extent)]
    axes=[(1.0,0.0),(0.0,1.0)]
    for first,second in zip(points,points[1:]+points[:1]):
        edge=(second[0]-first[0],second[1]-first[1])
        if edge!=(0.0,0.0):
            axes.append((-edge[1],edge[0]))
    for axis_x,axis_z in axes:
        polygon_projection=[x*axis_x+z*axis_z for x,z in points]
        square_projection=[x*axis_x+z*axis_z for x,z in square]
        if (max(polygon_projection)<min(square_projection) or
                max(square_projection)<min(polygon_projection)):
            return False
    return True
