import json
import click
import subprocess as sub
import os
from pathlib import Path
from getpass import getpass
from passlib.context import CryptContext
import passlib.handlers.pbkdf2

""" Programa para crear carpetas con contraseñas - APP CLI (Beta-v: 1.0) """

####### Configuraciónes del programa ########

dict_mode = {"show": "-h", "hide": "+h"}

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

def encrypt_password(password):
    return pwd_context.hash(password)


def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)


def read_folders():
    with open("folder.json", "r") as file:
        content = json.load(file)
        return content

def save_folder(folders):
    with open("folder.json", "w") as file:
        content = json.dumps(folders, indent=4)
        file.write(content)

def validate_folder(name):
    with open("folder.json", "r") as file:
        content = json.load(file)

        try:
            content[name]
            return True 
        
        except KeyError:
            return False

############## Función Principal ############
@click.group()
def main():
    pass

@click.command()
@click.option("-m", "--mode", default="show", type=click.Choice(["show", "hide"]), required=True, prompt="Modo")
@click.option("-n", "--name", type=str, help="Nombre de la carpeta a realizar la acción", required=True, prompt="Nombre")
def secure_folder(mode, name):

    """ Ocultar/Mostrar carpeta con su nombre """

    #Comandos equivalentes a los modos
    symbol = {"show": "-h", "hide": "+h"}

    #Obtenemos la información de las carpetas
    dict_folder = read_folders()

    #Comprobamos si esa carpeta existe
    if not validate_folder(name):
        click.echo("\nError: esa carpeta no esta registrada!")
        return

    #Comprobamos el estado y la modalidad concuerdan
    stat = "show" if dict_folder[name]["show"] == True else "hide"
    if stat == mode:
        click.echo(f"\nError: esta acción no se puede hacer...")
        return

    #Sistema de contraseña
    user_password = getpass("\nContraseña: ")

    if not check_encrypted_password(user_password, dict_folder[name]["password"]):
        click.echo("Contraseña incorrecta!")
        return

    #Ejecutamos la acción
    sub.call(["attrib", symbol[mode], name], cwd=dict_folder[name]["path"])

    #Actualizamos el estado de la carpeta
    if mode == "hide":
        dict_folder[name]["show"] = False

    elif mode == "show":
        dict_folder[name]["show"] = True

    #Guardamos cambios
    save_folder(dict_folder)

    click.echo(f"\n{name} ha sido '{mode}' con exito!")

@click.command()
def list_folders():

    """ Lista de carpetas seguras """
    
    #Leer archivo json
    content = read_folders()

    #Revisamos si la lista esta vacia
    if not content:
        click.echo("\nNo se han agregado carpetas...")
        return

    #Mostrar los datos
    print("######################## Lista de Carpetas ########################")
    for k, v in content.items():
        stat = "show" if v["show"] == True else "hide"
        click.echo(f"\n{k} = {v['path']} ({stat})")

    print("####################################################################")

@click.command()
@click.password_option(help="Nueva contraseña de la carpeta", prompt="Nueva contraseña")
@click.option("-n", "--name", help="Nombre de la carpeta a cambiar la contraseña", required=True, prompt="Nombre")
def folder_password(name, password):

    """ Modificar la contraseña de una carpeta """

    #Comprobamos si esa carpeta esta registrada
    if not validate_folder(name):
        click.echo("\nEsa carpeta no esta registrada...")
        return

    #Sistema de seguridad utilizando la contraseña anteriormente establecida
    content = read_folders()

    #Confirmamos la contraseña establecida anteriormente
    yes_password = getpass("\nConfirma contraseña: ")

    if not check_encrypted_password(yes_password, content[name]["password"]):
        click.echo("\nContraseña incorrecta!")
        return

    #Establecemos la nueva contraseña
    content[name]["password"] = encrypt_password(password)

    #Guardamos los cambios
    save_folder(content)

    click.echo("\nContraseña establecida con exito!")

@click.command()
@click.option("-n", "--name", help="Nombre de la carpeta", required=True, prompt="Nombre")
@click.password_option()
def add_folder(name, password):

    """ Agregar una carpeta al sistema de seguridad """

    #Encriptamos hash la contraseña
    hash = encrypt_password(password)

    #Revisamos que no sea una carpeta ya agregada
    if validate_folder(name) == True:
        click.echo("\nEsta carpeta ya fue agregada...")
        return

    #Obtener la ruta a traves del nombre
    ruta_abs = str(Path(os.path.abspath(name)).parent)

    #Comprobamos si existe la ruta
    if not os.path.exists(ruta_abs):
        click.echo("\nError: esa carpeta no existe...")
        return

    #Guardamos la carpeta
    content = read_folders()

    #En caso de que existan carpetas con el mismo nombre
    count = 0
    for key in content.keys():
        if key == name:
            count+=1
    
        name = f"{name}_{count}"
        break

    #Información de la carpeta
    content[name] = {"path": ruta_abs, "password": hash, "show": True}

    print(content[name])

    #Guardamos la nueva carpeta agregada
    save_folder(content)

    click.echo("\nCarpeta segura creada con exito!")


#Añadimos todos los comandos
main.add_command(add_folder)
main.add_command(list_folders)

if __name__ == "__main__":
    #Comprobamos si no se han registrado carpetas
    with open("folder.json", "r") as file:
        folders = json.load(file)

        if folders:
            main.add_command(folder_password)
            main.add_command(secure_folder)

    main()