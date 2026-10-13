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
    # Field chunks use one static root. Reject animated/hierarchical props.
    nodes=dictionary(data,model+64)
    if len(nodes)!=1: raise ValueError('Non-static field skeleton')
    node=model+64+nodes[0][1]
    flags=struct.unpack_from('<H',data,node)[0]
    translation=[0.,0.,0.];root_scale=[1.,1.,1.];rotation=[[float(i==j) for j in range(3)] for i in range(3)]
    cursor=node+4
    if not flags&1:
        translation=[v/4096 for v in struct.unpack_from('<3i',data,cursor)];cursor+=12
    if not flags&2:
        if flags&8:raise ValueError('Compact root rotation unsupported')
        values=[struct.unpack_from('<h',data,node+2)[0]/4096]+[v/4096 for v in struct.unpack_from('<8h',data,cursor)]
        cursor+=16
        rotation=[[values[col*3+row] for col in range(3)] for row in range(3)]
    if not flags&4:root_scale=[v/4096 for v in struct.unpack_from('<3i',data,cursor)]
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
    result=[];at=model+sbc_off;material=None;billboard=False
    while at<model+mat_off:
        command=data[at];at+=1;op=command&31;flags=command>>5
        if op==0:continue
        if op==1:break
        if op==2:at+=2
        elif op==3:
            if data[at]!=0:raise ValueError('Non-root SBC matrix')
            at+=1
        elif op==4:material=data[at];at+=1
        elif op==5:
            mesh=data[at];at+=1
            if material is None or material>=len(pairs) or mesh>=len(meshes):raise ValueError('SBC mesh binding')
            for face in meshes[mesh]:
                transformed=[tuple(sum(rotation[row][col]*v[col]*root_scale[col] for col in range(3))+translation[row] for row in range(3))+v[3:] for v in face]
                result.append((tuple(pairs[material]),transformed))
                if billboard:
                    # Static crossed planes retain the ROM's tree texture as
                    # the native battle camera turns; no animation is invented.
                    crossed=[(v[2]-translation[2]+translation[0],v[1],translation[2]-(v[0]-translation[0]))+v[3:] for v in transformed]
                    result.append((tuple(pairs[material]),crossed))
        elif op==6:
            if data[at]!=0:raise ValueError('Non-root SBC node')
            at+=3+(1 if flags&1 else 0)+(1 if flags&2 else 0)
        elif op==11:pass  # Position scaling already applied to decoded vertices.
        elif op==8:
            if data[at]!=0:raise ValueError('Non-root billboard node')
            at+=1+(1 if flags&1 else 0)+(1 if flags&2 else 0);billboard=True
        else:raise ValueError(f'Unsupported SBC {op}')
    if not result:raise ValueError('No field faces')
    return result


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
