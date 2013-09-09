#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Requires Python 3.2 or higher
#
# Manages automatically generated material definitions for textures.
# Textures that are recognized are named D.png, N.png or S.png.
#

import argparse
from string import Template
import fnmatch
import os

def is_valid(material_file, material_name):
    """ Checks whether the specified material file contains the passed material name 

    :material_file: The path to the material file.
    :material_name: The name to look for.
    :returns: Whether the material file is valid.

    """
    with open(material_file) as f:
        for line in f:
            if material_name in line:
                return True
    return False

def has_alpha_diffuse_map(directory):
    """Returns whether there exists a diffuse texture with an alpha channel at the specified directory

    :directory: The path to the directory to check.
    :returns: Whether there exists a diffuse texture with an alpha channel at the specified directory.

    """
    diffuse_texture_path = os.path.join(directory, "D.png")
    if not os.path.isfile(diffuse_texture_path):
        return False
    with open(diffuse_texture_path, "rb") as f:
        header = f.read(26)
        if len(header) != 26:
            return False
        return header[25] == 6 # Means that it is RGBA format


def has_normal_map(directory):
    """Returns whether there exists a normal map texture at the specified directory.

    :directory: The path to the directory to check.
    :returns: Whether there exists a normal map texture at the specified directory.

    """
    return os.path.isfile(os.path.join(directory, "N.png"))

def has_specular_map(directory):
    """Returns whether there exists a specular map texture at the specified directory.

    :directory: The path to the directory to check.
    :returns: Whether there exists a specular map texture at the specified directory.

    """
    return os.path.isfile(os.path.join(directory, "S.png"))


def generate_material(directory, material_file, material_name):
    """Generates a material script file

    :directory: The path to the material directory.
    :material_file: The path of the material file.
    :material_name: The name of the material as used inside the material script.

    """
    print("---- Generating material file {0}".format(material_file))

    reldir = os.path.relpath(directory, os.getcwd())
    specular = has_specular_map(directory)
    normal = has_normal_map(directory)
    alpha = has_alpha_diffuse_map(directory)

    parent_material = "/base/simple"
    if normal and specular:
        parent_material = "/base/normalmap/specular"
    elif normal:
        parent_material = "/base/normalmap"
# We assume that all alpha materials are nonculled -- TODO
    if alpha:
        parent_material += "/nonculled/alpharejected"


    material = "import * from \"resources/ogre/scripts/materials/base.material\"\n"

    if alpha:
        material += "import * from \"resources/ogre/scripts/programs/DepthShadowmap.material\"\n"
        material += "material ${name}/shadowcaster : Ogre/DepthShadowmap/Caster/Float\n{\n"
        material += "    set_texture_alias DiffuseMap ${reldir}/D.png\n}\n"
    material += "material $name : $parent\n{\n"
    material += "    set_texture_alias DiffuseMap ${reldir}/D.png\n"
    if alpha:
        material += "    set $$shadow_caster_material ${name}/shadowcaster\n"

    if normal:
        material += "    set_texture_alias NormalHeightMap ${reldir}/N.png\n"
    if specular:
        material += "    set_texture_alias SpecularMap ${reldir}/S.png\n"
    material  += "}"

    params = {
            'name' : material_name,
            'parent' : parent_material,
            'reldir' : reldir
            }

    material = Template(material).substitute(params)

    with open(material_file, 'w') as f:
        f.write(material)
        f.flush()


def main():
    """The main entry point."""
    modes = ["find-missing",
            "create-missing",
            "find-invalid",
            "refresh"]

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=modes)
    args = parser.parse_args()


    diffuse_textures =  [os.path.join(dirpath, f)
            for dirpath, dirnames, files in os.walk(os.getcwd())
            for f in fnmatch.filter(files, 'D.png')]

    for diffuse_texture in diffuse_textures:
        directory = os.path.dirname(diffuse_texture)
        material_file = os.path.join(directory, 'ogre.material')
        material_name = os.path.relpath(directory, os.getcwd())
        material_name = material_name.replace('textures/', '')
        material_name = material_name.replace('3d_objects/', '')
        material_name = material_name.replace('3d_skeletons/', '')
        material_name = '/global/' + material_name

        if not os.path.isfile(material_file):
            if  args.mode == "find-missing":
                print(material_file)
            elif args.mode == "create-missing":
                generate_material(directory, material_file, material_name)
        elif args.mode == "refresh":
            os.remove(material_file)
            generate_material(directory, material_file, material_name)
        elif args.mode == "find-invalid":
            if not is_valid(material_file, material_name):
                print(material_file)

    pass

if __name__ == '__main__':
    main()
