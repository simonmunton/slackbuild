#!BPY

"""
Name: '3D Studio'
Blender: 233
Group: 'Export'
Tip: 'Export to 3DS file format. (.3ds)'
"""



######################################################
# 3ds Importer
# By:  Bob Holcomb and Richard Lärkäng
# Date: 22 APR 04
# Ver: 0.7
######################################################
# This script imports a 3ds file and the materials
#  into blender for editing.  Hopefully
# this will make it into a future version as an import
# feature of the menu.  Loader is based on 3ds loader
# from www.gametutorials.com(Thanks DigiBen).
######################################################

######################################################
# Importing modules
######################################################

import Blender
from Blender import NMesh, Scene, Object, Material
from Blender.BGL import *
from Blender.Draw import *
from Blender.Window import *
from Blender.Image import *
from Blender.Material import *

import sys, struct, string, types, math
from types import *

import os
from os import path


######################################################
# Data Structures
######################################################

#Some of the chunks that we will see
#----- Primary Chunk, at the beginning of each file
PRIMARY=19789 				#0x4D4D

#------ Main Chunks
OBJECTINFO=15677				#0x3D3D			// This gives the version of the mesh and is found right before the material and object information
VERSION=2					#0x0002			// This gives the version of the .3ds file
EDITKEYFRAME=45056			#0xB000			// This is the header for all of the key frame info

#------ sub defines of OBJECTINFO
MATERIAL=45055				#0xAFFF			// This stored the texture info
OBJECT=16384					#0x4000			// This stores the faces, vertices, etc...

#------ sub defines of MATERIAL
MATNAME=40960				#0xA000			// This holds the material name
MATAMBIENT=40976			#0xA010
MATDIFFUSE=40992				#0xA020			// This holds the color of the object/material
MATSPECULAR=41008			#0xA030
MATMAP=41472				#0xA200			// This is a header for a new material
MATMAPFILE=41728				#0xA300			// This holds the file name of the texture

RGB1=17					#0x0011
RGB2=18					#0x0012

OBJECT_MESH=16640			#0x4100			// This lets us know that we are reading a new object

#------ sub defines of OBJECT_MESH
OBJECT_VERTICES=16656			#0x4110			// The objects vertices
OBJECT_FACES=16672			#0x4120			// The objects faces
OBJECT_MATERIAL=16688		#0x4130			// This is found if the object has a material, either texture map or color
OBJECT_UV=16704				#0x4140			// The UV texture coordinates
OBJECT_TRANS_MATRIX=16736	#0x4160			// The translation matrix of the object 54 bytes

def point_by_matrix(p, m):
  return [p[0] * m[0][0] + p[1] * m[1][0] + p[2] * m[2][0] + m[3][0],
          p[0] * m[0][1] + p[1] * m[1][1] + p[2] * m[2][1] + m[3][1],
          p[0] * m[0][2] + p[1] * m[1][2] + p[2] * m[2][2] + m[3][2]]

#the chunk class
class chunk:
	ID=0
	size=0

	def __init__(self):
		self.ID=0
		self.size=0

	def get_size(self):
		self.size=6

	def write(self, file):
		binary_format="<HI"  #all header info looks like this
		#calculate size
		temp_data=[0]*2
		temp_data[0]=self.ID
		temp_data[1]=self.size
		#write header
		data=struct.pack(binary_format,temp_data[0],temp_data[1])
		file.write(data)

	def dump(self):
		print "ID: ", self.ID
		print "ID in hex: ", hex(self.ID)
		print "size: ", self.size



#may want to add light, camera, keyframe chunks.
class vert_chunk(chunk):
	verts=[]

	def __init__(self):
		self.verts=[]
		self.ID=OBJECT_VERTICES

	def get_size(self):
		chunk.get_size(self)
		temp_size=2 #for the number of verts short
		for vert in self.verts:
			temp_size+=12  #3 floats x 4 bytes each
		self.size+=temp_size
		print "vert_chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		binary_format="<H"
		temp_data=[0]
		temp_data[0]=len(self.verts)
		#write header
		data=struct.pack(binary_format,temp_data[0])
		file.write(data)
		#write verts
		for vert in self.verts:
			binary_format="<3f"
			temp_data=[0.0]*3
			temp_data[0]=vert[0]
			temp_data[1]=vert[1]
			temp_data[2]=vert[2]
			data=struct.pack(binary_format,temp_data[0],temp_data[1], temp_data[2])
			file.write(data)

class obj_material_chunk(chunk):
	name=""
	faces=[]

	def __init__(self):
		self.name=""
		self.faces=[]
		self.ID=OBJECT_MATERIAL

	def get_size(self):
		chunk.get_size(self)
		temp_size=(len(self.name)+1)
		temp_size+=2
		for face in self.faces:
			temp_size+=2
		self.size+=temp_size
		print "obj material chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write name
		name_length=len(self.name)+1
		binary_format="<"+str(name_length)+"s"
		data=struct.pack(binary_format, self.name)
		file.write(data)
		binary_format="<H"
		print "Nr of faces: ", len(self.faces)
		data=struct.pack(binary_format, len(self.faces))
		file.write(data)
		for face in self.faces:
			data=struct.pack(binary_format, face)
			file.write(data)

class face_chunk(chunk):
	faces=[]
	num_faces=0
	m_chunks=[]

	def __init__(self):
		self.faces=[]
		self.ID=OBJECT_FACES
		self.num_faces=0
		self.m_chunks=[]

	def get_size(self):
		chunk.get_size(self)
		temp_size=2 #num faces info
		for face in self.faces:
			temp_size+=8  #4 short ints x 2 bytes each
		for m in self.m_chunks:
			temp_size+=m.get_size()
		self.size+=temp_size
		print "face_chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		binary_format="<H"
		temp_data=[0]
		temp_data[0]=len(self.faces)
		data=struct.pack(binary_format,temp_data[0])
		file.write(data)
		#write faces
		for face in self.faces:
			binary_format="<4H"
			temp_data=[0]*4
			temp_data[0]=face[0]
			temp_data[1]=face[1]
			temp_data[2]=face[2]
			temp_data[3]=0 #only used by 3d studio
			data=struct.pack(binary_format,temp_data[0],temp_data[1], temp_data[2], temp_data[3])
			file.write(data)
		#write materials
		for m in self.m_chunks:
			m.write(file)

class uv_chunk(chunk):
	uv=[]
	num_uv=0

	def __init__(self):
		self.uv=[]
		self.ID=OBJECT_UV
		self.num_uv=0

	def get_size(self):
		chunk.get_size(self)
		temp_size=2 #for num UV
		for this_uv in self.uv:
			temp_size+=8  #2 floats at 4 bytes each
		self.size+=temp_size
		print "uv chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		binary_format="<H"
		temp_data=[0]
		temp_data[0]=len(self.uv)
		#write header
		data=struct.pack(binary_format,temp_data[0])
		file.write(data)
		#write verts
		for this_uv in self.uv:
			binary_format="<2f"
			temp_data=[0.0]*2
			temp_data[0]=this_uv[0]
			temp_data[1]=this_uv[1]
			data=struct.pack(binary_format,temp_data[0],temp_data[1])
			file.write(data)

class mesh_chunk(chunk):
	v_chunk=vert_chunk()
	f_chunk=face_chunk()
	uv_chunk=uv_chunk()

	def __init__(self):
		self.v_chunk=vert_chunk()
		self.f_chunk=face_chunk()
		self.uv_chunk=uv_chunk()
		self.ID=OBJECT_MESH

	def get_size(self):
		chunk.get_size(self)
		temp_size=self.v_chunk.get_size()
		temp_size+=self.f_chunk.get_size()
		temp_size+=self.uv_chunk.get_size()
		self.size+=temp_size
		print "object mesh chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write stuff
		self.v_chunk.write(file)
		self.f_chunk.write(file)
		self.uv_chunk.write(file)

class object_chunk(chunk):
	name=""
	mesh_chunks=[]

	def __init__(self):
		self.name=""
		self.mesh_chunks=[]
		self.ID=OBJECT

	def get_size(self):
		chunk.get_size(self)
		temp_size=len(self.name)+1 #+1 for null character
		for mesh in self.mesh_chunks:
			temp_size+=mesh.get_size()
		self.size+=temp_size
		print "object chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write name
		name_length=len(self.name)+1
		binary_format="<"+str(name_length)+"s"
		data=struct.pack(binary_format, self.name)
		file.write(data)
		#write stuff
		for mesh in self.mesh_chunks:
			mesh.write(file)

class object_info_chunk(chunk):
	obj_chunks=[]
	mat_chunks=[]

	def __init__(self):
		self.obj_chunks=[]
		self.mat_chunks=[]
		self.ID=OBJECTINFO

	def get_size(self):
		chunk.get_size(self)
		temp_size=0
		for mat in self.mat_chunks:
			temp_size+=mat.get_size()
		for obj in self.obj_chunks:
			temp_size+=obj.get_size()
		self.size+=temp_size
		print "object info size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write all the materials
		for mat in self.mat_chunks:
			mat.write(file)
		#write all the objects
		for obj in self.obj_chunks:
			obj.write(file)



class version_chunk(chunk):
	version=3

	def __init__(self):
		self.ID=VERSION
		self.version=3 #that the document that I'm using

	def get_size(self):
		chunk.get_size(self)
		temp_size=4 #bytes for the version info
		self.size+=temp_size
		print "version chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		binary_format="<I"
		temp_data=[0]
		temp_data[0]=self.version
		#write header and version
		data=struct.pack(binary_format,temp_data[0])
		file.write(data)

class rgb_chunk(chunk):
	col=[]

	def __init__(self):
		self.col=[]

	def get_size(self):
		chunk.get_size(self)
		temp_size=3  #color size
		self.size+=temp_size
		print "rgb chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		binary_format="<c"
		#write colors
		for i in [0, 1, 2]:
			data=struct.pack(binary_format,chr(255*self.col[i]))
			file.write(data)


class rgb1_chunk(rgb_chunk):

	def __init__(self):
		self.ID=RGB1

class rgb2_chunk(rgb_chunk):

	def __init__(self):
		self.ID=RGB2

class material_ambient_chunk(chunk):
	col1=None
	col2=None

	def __init__(self):
		self.ID=MATAMBIENT
		self.col1=rgb1_chunk()
		self.col2=rgb2_chunk()

	def get_size(self):
		chunk.get_size(self)
		temp_size=self.col1.get_size()
		temp_size+=self.col2.get_size()
		self.size+=temp_size
		print "material ambient size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write colors
		self.col1.write(file)
		self.col2.write(file)

class material_diffuse_chunk(chunk):
	col1=None
	col2=None

	def __init__(self):
		self.ID=MATDIFFUSE
		self.col1=rgb1_chunk()
		self.col2=rgb2_chunk()

	def get_size(self):
		chunk.get_size(self)
		temp_size=self.col1.get_size()
		temp_size+=self.col2.get_size()
		self.size+=temp_size
		print "material diffuse size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write colors
		self.col1.write(file)
		self.col2.write(file)

class material_specular_chunk(chunk):
	col1=None
	col2=None

	def __init__(self):
		self.ID=MATSPECULAR
		self.col1=rgb1_chunk()
		self.col2=rgb2_chunk()

	def get_size(self):
		chunk.get_size(self)
		temp_size=self.col1.get_size()
		temp_size+=self.col2.get_size()
		self.size+=temp_size
		print "material specular size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write colors
		self.col1.write(file)
		self.col2.write(file)

class material_name_chunk(chunk):
	name=""

	def __init__(self):
		self.ID=MATNAME
		self.name=""

	def get_size(self):
		chunk.get_size(self)
		temp_size=(len(self.name)+1)
		self.size+=temp_size
		print "material name size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write name
		name_length=len(self.name)+1
		binary_format="<"+str(name_length)+"s"
		data=struct.pack(binary_format, self.name)
		file.write(data)

class material_chunk(chunk):
	matname_chunk=None
	matambient_chunk=None
	matdiffuse_chunk=None
	matspecular_chunk=None

	def __init__(self):
		self.ID=MATERIAL
		self.matname_chunk=material_name_chunk()
		self.matambient_chunk=material_ambient_chunk()
		self.matdiffuse_chunk=material_diffuse_chunk()
		self.matspecular_chunk=material_specular_chunk()

	def get_size(self):
		chunk.get_size(self)
		temp_size=self.matname_chunk.get_size()
		temp_size+=self.matambient_chunk.get_size()
		temp_size+=self.matdiffuse_chunk.get_size()
		temp_size+=self.matspecular_chunk.get_size()
		self.size+=temp_size
		print "material chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write name chunk
		self.matname_chunk.write(file)
		#write material colors
		self.matambient_chunk.write(file)
		self.matdiffuse_chunk.write(file)
		self.matspecular_chunk.write(file)

class primary_chunk(chunk):
	version=None
	obj_info=None

	def __init__(self):
		self.version=version_chunk()
		self.obj_info=object_info_chunk()
		self.ID=PRIMARY

	def get_size(self):
		chunk.get_size(self)
		temp_size=self.version.get_size()
		temp_size+=self.obj_info.get_size()
		self.size+=temp_size
		print "primary chunk size: ", self.size
		return self.size

	def write(self, file):
		chunk.write(self, file)
		#write version chunk
		self.version.write(file)
		#write object_info chunk
		self.obj_info.write(file)

def read_chunk(file, chunk):
		temp_data=file.read(struct.calcsize(chunk.binary_format))
		data=struct.unpack(chunk.binary_format, temp_data)
		chunk.ID=data[0]
		chunk.size=data[1]

		#if debugging
		#chunk.dump()

def read_string(file):
	s=""
	index=0
	#print "reading a string"
	#read in the characters till we get a null character
	temp_data=file.read(struct.calcsize("c"))
	data=struct.unpack("c", temp_data)
	s=s+(data[0])
	#print "string: ",s
	while(ord(s[index])!=0):
		index+=1
		temp_data=file.read(struct.calcsize("c"))
		data=struct.unpack("c", temp_data)
		s=s+(data[0])
		#print "string: ",s
	return str(s)

######################################################
# EXPORT
######################################################
def save_3ds(filename):

	vert_list={}
	vert_count=0
	#open the current scene
	scene = Blender.Scene.GetCurrent()
	#if the user was lazy and didn't add a filename,
	#just name the files after the scene name
	#hope they weren't lazy there too.
	if filename=="model":
		filename=scene.getName()
		#basefilename and /path/filename are the same
		bfilename=filename
	else:
		#extract the actual filename from the
		#entire path of the /path/filename
		bfilename = os.path.basename(filename)

	exported_materials = []

	#fill the chunks full of data
	primary=primary_chunk()
	#get all the objects in this scene
	object_list=Blender.Object.Get()
	#fill up the data structures with objects
	for obj in object_list:
		#create a new object chunk
		if obj.getType()=="Mesh":
			primary.obj_info.obj_chunks.append(object_chunk())
			#get the mesh data
			blender_mesh=obj.getData()
			#set the object name
			primary.obj_info.obj_chunks[len(primary.obj_info.obj_chunks)-1].name=obj.getName()

			matrix = obj.getMatrix()

			#make a new mesh chunk object
			mesh=mesh_chunk()

			#fill verts in
			vert_count=0
			vert_list={}
			for vert in blender_mesh.verts:
				# get the vertex and apply all transforms to it
				v = point_by_matrix(vert.co, matrix)
				vert_key=(v[0], v[1], v[2])
				mesh.v_chunk.verts.append(vert_key)
				if not vert_list.has_key(vert_key):
					#print "didn't have the key"
					vert_list[vert_key] = vert_count  #save this info for the face lookup table
					vert_count = vert_count + 1

			print "vert_count: ", vert_count
			print "mesh.verts: ", len(blender_mesh.verts)

			for m in blender_mesh.materials:
				mesh.f_chunk.m_chunks.append(obj_material_chunk())
				mesh.f_chunk.m_chunks[len(mesh.f_chunk.m_chunks)-1].name = m.name

				# materials should only be exported once
				if m.name in exported_materials:
					continue

				material = material_chunk()
				material.matname_chunk.name=m.name
				material.matambient_chunk.col1.col = m.mirCol
				material.matambient_chunk.col2.col = m.mirCol
				material.matdiffuse_chunk.col1.col = m.rgbCol
				material.matdiffuse_chunk.col2.col = m.rgbCol
				material.matspecular_chunk.col1.col = m.specCol
				material.matspecular_chunk.col2.col = m.specCol

				primary.obj_info.mat_chunks.append(material)

				exported_materials.append(m.name)


			facenr=0
			#fill in faces
			for face in blender_mesh.faces:
				#is this a tri or a quad
				num_fv=len(face.v)
				
				#it's a tri
				if num_fv==3:
					indexes=[0]*3
					for i in range (0,3):
						#build the keys
						# get the vertex and apply all transforms to it
						vert=point_by_matrix(face.v[i].co, matrix)
						vert_key=(vert[0], vert[1], vert[2])
						#look up the key to get the index
						vert_index=vert_list[vert_key]
						indexes[i]=vert_index
					mesh.f_chunk.faces.append(indexes)
					if (face.materialIndex < len(mesh.f_chunk.m_chunks)):
						mesh.f_chunk.m_chunks[face.materialIndex].faces.append(facenr)
					facenr+=1
					
				#it's a quad
				elif num_fv==4:
					indexes=[0]*4
					for i in range (0,4):
						#build the keys
						vert=point_by_matrix(face.v[i].co, matrix)
						vert_key=(vert[0], vert[1], vert[2])
						#look up the key to get the index
						vert_index=vert_list[vert_key]
						indexes[i]=vert_index
						first_tri=(indexes[0], indexes[1], indexes[2])
						sec_tri=(indexes[2], indexes[3], indexes[0])
						
					mesh.f_chunk.faces.append(first_tri)  # 0,1,2
					mesh.f_chunk.faces.append(sec_tri)  # 2,3,0
					#first tri
					if (face.materialIndex < len(mesh.f_chunk.m_chunks)):
						mesh.f_chunk.m_chunks[face.materialIndex].faces.append(facenr)
					facenr+=1
					#other tri
					if (face.materialIndex < len(mesh.f_chunk.m_chunks)):
						mesh.f_chunk.m_chunks[face.materialIndex].faces.append(facenr)
					facenr+=1


			#fill in the UV info
			if blender_mesh.hasVertexUV():
				for vert in blender_mesh.verts:
					uv_coord=(vert.uvco)
					mesh.uv_chunk.uv.append((uv_coord[0], uv_coord[1]))

			elif blender_mesh.hasFaceUV():
				for face in blender_mesh.faces:
					num_fv=len(face.v)
					if num_fv==3:
						for i in range (0,3):
							uv_coord=(face.uv[i])
							mesh.uv_chunk.uv.append((uv_coord[0], uv_coord[1]))
					elif num_fv==4:
						for i in range (0,4):
							uv_coord=(face.uv[i])
							mesh.uv_chunk.uv.append((uv_coord[0], uv_coord[1]))


			#filled in our mesh, lets add it to the file
			primary.obj_info.obj_chunks[len(primary.obj_info.obj_chunks)-1].mesh_chunks.append(mesh)

	#check the size
	primary.get_size()
	#open the files up for writing
	file = open( filename, "wb" )
	#recursively write the stuff to file
	primary.write(file)
	file.close()

#***********************************************
# MAIN
#***********************************************

	
def my_callback(filename):
	if(filename.find('.3ds', -4) <= 0):
		filename += '.3ds'
	save_3ds(filename)

Blender.Window.FileSelector(my_callback, "Export 3DS")
