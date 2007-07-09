#!BPY

""" 
Name: '3D Studio'
Blender: 233
Group: 'Import'
Tip: 'Import from 3DS file format. (.3ds)'
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

import sys, struct, string, types
from types import *

import os
from os import path


######################################################
# Data Structures
######################################################

#Some of the chunks that we will see
#----- Primary Chunk, at the beginning of each file
PRIMARY=19789 #0x4D4D

#------ Main Chunks
OBJECTINFO=15677	#0x3D3D				// This gives the version of the mesh and is found right before the material and object information
VERSION=2			#0x0002				// This gives the version of the .3ds file
EDITKEYFRAME=45056	#0xB000				// This is the header for all of the key frame info

#------ sub defines of OBJECTINFO
MATERIAL=45055		#0xAFFF				// This stored the texture info
OBJECT=16384		#0x4000				// This stores the faces, vertices, etc...

#------ sub defines of MATERIAL
MATNAME=40960		#0xA000				// This holds the material name
MATAMBIENT=40976	#0xA010
MATDIFFUSE=40992	#0xA020				// This holds the color of the object/material
MATSPECULAR=41008	#0xA030
MATMAP=41472		#0xA200				// This is a header for a new material
MATMAPFILE=41728	#0xA300				// This holds the file name of the texture

OBJECT_MESH=16640	#0x4100				// This lets us know that we are reading a new object

#------ sub defines of OBJECT_MESH
OBJECT_VERTICES=16656	#0x4110			// The objects vertices
OBJECT_FACES=16672		#0x4120			// The objects faces
OBJECT_MATERIAL=16688	#0x4130			// This is found if the object has a material, either texture map or color
OBJECT_UV=16704			#0x4140			// The UV texture coordinates
OBJECT_TRANS_MATRIX=16736	#0x4160		// The translation matrix of the object 54 bytes

#the chunk class
class chunk:
	ID=0
	length=0
	bytes_read=0

	#we don't read in the bytes_read, we compute that
	binary_format="<HI"


	def __init__(self):
		self.ID=0
		self.length=0
		self.bytes_read=0

	def dump(self):
		print "ID: ", self.ID
		print "ID in hex: ", hex(self.ID)
		print "length: ", self.length
		print "bytes_read: ", self.bytes_read


def read_chunk(file, chunk):
		temp_data=file.read(struct.calcsize(chunk.binary_format))
		data=struct.unpack(chunk.binary_format, temp_data)
		chunk.ID=data[0]
		chunk.length=data[1]
		#update the bytes read function
		chunk.bytes_read=6

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
	
	#remove the null character from the string
	the_string=s[:-1]
	return str(the_string)

######################################################
# IMPORT
######################################################
def process_next_object_chunk(file, previous_chunk, mesh):
	new_chunk=chunk()
	temp_chunk=chunk()

	while (previous_chunk.bytes_read<previous_chunk.length):
		#read the next chunk
		read_chunk(file, new_chunk)

		if (new_chunk.ID==OBJECT_MESH):
			print "Found an OBJECT_MESH chunk"
			print "object_mesh: lenght: ", new_chunk.length
			process_next_object_chunk(file, new_chunk, mesh)
			print "object mesh: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID==OBJECT_VERTICES):
			print "Found an OBJECT_VERTICES chunk"
			print "object_verts: lenght: ", new_chunk.length
			temp_data=file.read(struct.calcsize("H"))
			data=struct.unpack("H", temp_data)
			new_chunk.bytes_read+=2
			num_verts=data[0]
			print "number of verts: ", num_verts
			for counter in range (0,num_verts):
				temp_data=file.read(struct.calcsize("3f"))
				new_chunk.bytes_read+=12 #3 floats x 4 bytes each
				data=struct.unpack("3f", temp_data)
				v=NMesh.Vert(data[0],data[1],data[2])
				mesh.verts.append(v)
			print "object verts: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID==OBJECT_FACES):
			print "Found an OBJECT_FACES chunk"
			print "object faces: lenght: ", new_chunk.length
			temp_data=file.read(struct.calcsize("H"))
			data=struct.unpack("H", temp_data)
			new_chunk.bytes_read+=2
			num_faces=data[0]
			print "number of faces: ", num_faces

			for counter in range(0,num_faces):
				temp_data=file.read(struct.calcsize("4H"))
				new_chunk.bytes_read+=8 #4 short ints x 2 bytes each
				data=struct.unpack("4H", temp_data)
				#insert the mesh info into the faces, don't worry about data[3] it is a 3D studio thing
				f=NMesh.Face()
				f.v.append(mesh.verts[data[0]])
				f.v.append(mesh.verts[data[1]])
				f.v.append(mesh.verts[data[2]])
				mesh.faces.append(f)
			print "object faces: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID==OBJECT_MATERIAL):
			print "Found an OBJECT_MATERIAL chunk"
			print "object material: length: ", new_chunk.length
			material_name=""
			material_name=str(read_string(file))
			#plus one for the null character that gets removed
			new_chunk.bytes_read+=(len(material_name)+1)
			print "material_name: ", material_name

			#look up the material in all the materials
			material_found=0
			for mat in Material.Get():
				
				#found it, add it to the mesh
				if(mat.name==material_name):
					if(len(mesh.materials)>=15):
						result=Blender.Draw.PupMenu("Cannot assign more than 16 materials to a mesh: Continue?%t|OK")
						break;
					else:
						mesh.addMaterial(mat)
						material_found=1
						print "found material: ",mat.name
						
						#figure out what material index this is for the mesh
						for mat_counter in range(0,len(mesh.materials)):
							if mesh.materials[mat_counter].name==material_name:
								mat_index=mat_counter
								print "material index: ",mat_index
						
						#break out of this for loop so we don't accidentally set material_found back to 0
						break
				else:
					material_found=0
					#print "Not matching: ", mat.name, " and ", material_name

			if(material_found==1):
				#read the number of faces using this material
				temp_data=file.read(struct.calcsize("H"))
				data=struct.unpack("H", temp_data)
				new_chunk.bytes_read+=2
				num_faces_using_mat=data[0]
				print "number of faces using this material: ", num_faces_using_mat

				#list of faces using mat
				for face_counter in range(0,num_faces_using_mat):
					temp_data=file.read(struct.calcsize("H"))
					new_chunk.bytes_read+=2
					data=struct.unpack("H", temp_data)
					#print "face #: ", data[0]
					mesh.faces[data[0]].materialIndex=mat_index
					
			else:
				#read past the information about the material you couldn't find
				print "Couldn't find material.  Reading past face material info"
				buffer_size=new_chunk.length-new_chunk.bytes_read
				binary_format=str(buffer_size)+"c"
				temp_data=file.read(struct.calcsize(binary_format))
				new_chunk.bytes_read+=buffer_size
			
			print "object mat: bytes read: ", new_chunk.bytes_read

		elif (new_chunk.ID==OBJECT_UV):
			print "Found an OBJECT_UV chunk"
			print "object uv: lenght: ", new_chunk.length
			temp_data=file.read(struct.calcsize("H"))
			data=struct.unpack("H", temp_data)
			new_chunk.bytes_read+=2
			num_uv=data[0]
			print "number of UV: ", num_uv

			for counter in range(0,num_uv):
				temp_data=file.read(struct.calcsize("2f"))
				new_chunk.bytes_read+=8 #2 float x 4 bytes each
				data=struct.unpack("2f", temp_data)
				#insert the insert the UV coords in the vertex data
				mesh.verts[counter].uvco[0]=data[0]
				mesh.verts[counter].uvco[1]=data[1]
			#turn on the sticky UV coords for this mesh
			mesh.hasVertexUV(1)
			print "object uv: bytes read: ", new_chunk.bytes_read

		else:
			print "Found some other Object chunk: ",hex(new_chunk.ID)
			print "object faces: length: ", new_chunk.length
			buffer_size=new_chunk.length-new_chunk.bytes_read
			binary_format=str(buffer_size)+"c"
			temp_data=file.read(struct.calcsize(binary_format))
			new_chunk.bytes_read+=buffer_size
			print "object other: bytes read: ", new_chunk.bytes_read

		previous_chunk.bytes_read+=new_chunk.bytes_read
		print "Bytes left in this Object chunk: ", previous_chunk.length-previous_chunk.bytes_read

def process_next_material_chunk(file, previous_chunk, mat):
	new_chunk=chunk()
	temp_chunk=chunk()

	while (previous_chunk.bytes_read<previous_chunk.length):
		#read the next chunk
		read_chunk(file, new_chunk)

		if (new_chunk.ID==MATNAME):
			print "Found a MATNAME chunk"
			material_name=""
			material_name=str(read_string(file))
			
			#plus one for the null character that ended the string
			new_chunk.bytes_read+=(len(material_name)+1)
			print "material_name: ", material_name
			
			mat.setName(material_name)
			print "mat.name: ", mat.name

		elif (new_chunk.ID==MATAMBIENT):
			print "Found a MATAMBIENT chunk"

			read_chunk(file, temp_chunk)
			temp_data=file.read(struct.calcsize("3B"))
			data=struct.unpack("3B", temp_data)
			temp_chunk.bytes_read+=3
			r=data[0]
			g=data[1]
			b=data[2]
			mat.setMirCol(float(r)/255, float(g)/255, float(b)/255)
			new_chunk.bytes_read+=temp_chunk.bytes_read

		elif (new_chunk.ID==MATDIFFUSE):
			print "Found a MATDIFFUSE chunk"

			read_chunk(file, temp_chunk)
			temp_data=file.read(struct.calcsize("3B"))
			data=struct.unpack("3B", temp_data)
			temp_chunk.bytes_read+=3
			r=data[0]
			g=data[1]
			b=data[2]
			mat.setRGBCol(float(r)/255, float(g)/255, float(b)/255)
			new_chunk.bytes_read+=temp_chunk.bytes_read

		elif (new_chunk.ID==MATSPECULAR):
			print "Found a MATSPECULAR chunk"

			read_chunk(file, temp_chunk)
			temp_data=file.read(struct.calcsize("3B"))
			data=struct.unpack("3B", temp_data)
			temp_chunk.bytes_read+=3
			r=data[0]
			g=data[1]
			b=data[2]
			mat.setSpecCol(float(r)/255, float(g)/255, float(b)/255)
			new_chunk.bytes_read+=temp_chunk.bytes_read

		elif (new_chunk.ID==MATMAP):
			print "Found a MATMAP chunk"
			#recurse into this one
			process_next_material_chunk(file, new_chunk, mat)

		elif (new_chunk.ID==MATMAPFILE):
			print "Found a MATMAPFILE chunk"
			texture_name=""
			texture_name=str(read_string(file))
			
			#plus one for the null character that gets removed
			new_chunk.bytes_read+=(len(texture_name)+1)

		else:
			print "Found some other Material chunk: ",hex(new_chunk.ID)
			buffer_size=new_chunk.length-new_chunk.bytes_read
			binary_format=str(buffer_size)+"c"
			temp_data=file.read(struct.calcsize(binary_format))
			new_chunk.bytes_read+=buffer_size

		previous_chunk.bytes_read+=new_chunk.bytes_read
		print "Bytes left in this Material chunk: ", previous_chunk.length-previous_chunk.bytes_read

def process_next_chunk(file, previous_chunk):
	#a spare chunk
	new_chunk=chunk()
	temp_chunk=chunk()

	#loop through all the data for this chunk (previous chunk) and see what it is
	while (previous_chunk.bytes_read<previous_chunk.length):
		#read the next chunk
		print "reading a chunk"
		read_chunk(file, new_chunk)

		#is it a Version chunk?
		if (new_chunk.ID==VERSION):
			print "found a VERSION chunk"
			print "version: lenght: ", new_chunk.length
			#read in the version of the file
			#it's an unsigned short (H)
			temp_data=file.read(struct.calcsize("I"))
			data=struct.unpack("I", temp_data)
			version=data[0]
			new_chunk.bytes_read+=4 #read the 4 bytes for the version number
			#this loader works with version 3 and below, but may not with 4 and above
			if (version>3):
				print "Non-Fatal Error:  Version greater than 3, may not load correctly: ", version

		#is it an object info chunk?
		elif (new_chunk.ID==OBJECTINFO):
			print "found an OBJECTINFO chunk"
			print "object info: lenght: ", new_chunk.length
			#recursively go through the rest of the file
			process_next_chunk(file, new_chunk)

			#keep track of how much we read in the main chunk
			new_chunk.bytes_read+=temp_chunk.bytes_read

		#is it an object chunk?
		elif (new_chunk.ID==OBJECT):
			print "found an OBJECT chunk"
			print "object length: ", new_chunk.length
			#make a mesh
			mesh=NMesh.New()
			mesh.name=str(read_string(file))
			print "mesh name: ", mesh.name
			#plus one for the null character that gets removed
			new_chunk.bytes_read+=(len(mesh.name)+1)

			process_next_object_chunk(file, new_chunk, mesh)

			#put the object into blender at the cursor location
			mesh_obj=NMesh.PutRaw(mesh)
			cursor_pos=Blender.Window.GetCursorPos()
			mesh_obj.setLocation(float(cursor_pos[0]),float(cursor_pos[1]),float(cursor_pos[2]))

		#is it a material chunk?
		elif (new_chunk.ID==MATERIAL):
			print "found a MATERIAL chunk"
			
			material=Material.New()
			process_next_material_chunk(file, new_chunk, material)

		else: #(new_chunk.ID!=VERSION or new_chunk.ID!=OBJECTINFO or new_chunk.ID!=OBJECT or new_chunk.ID!=MATERIAL):
			print "skipping to end of this chunk"
			buffer_size=new_chunk.length-new_chunk.bytes_read
			binary_format=str(buffer_size)+"c"
			temp_data=file.read(struct.calcsize(binary_format))
			new_chunk.bytes_read+=buffer_size


		#update the previous chunk bytes read
		previous_chunk.bytes_read+=new_chunk.bytes_read
		print "Bytes left in this chunk: ", previous_chunk.length-previous_chunk.bytes_read


def load_3ds (filename):

	current_chunk=chunk()
	
	file=open(filename,"rb")
	
	#here we go!
	print "reading the first chunk"
	read_chunk(file, current_chunk)
	if (current_chunk.ID!=PRIMARY):
		print "Fatal Error:  Not a valid 3ds file: ", filename
		Exit()

	process_next_chunk(file, current_chunk)

	file.close()


#***********************************************
# MAIN
#***********************************************

	
def my_callback(filename):
	load_3ds(filename)

Blender.Window.FileSelector(my_callback, "Import 3DS")
