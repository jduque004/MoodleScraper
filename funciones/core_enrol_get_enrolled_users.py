#!/usr/bin/env python
import sys
import requests
from requests import session
from bs4 import BeautifulSoup
import json
import time


def main():
    global baseurl
    global destino
    if len(sys.argv) < 6:
        print('ERROR! Parámetros incorrectos')
        print('Formato de llamada: core_grading_get_definitions.py baseURL user pass courseid pathJSONResultado')
        str1 = 'Ejemplo de llamada: core_grading_get_definitions.py'
        str2 = ' http://localhost/moodle/ profesor2 Profesor2* 2 D:\\resultscraper.json'
        print(str1 + str2)
        sys.exit()
    else:
        baseurl = sys.argv[1]
        username = sys.argv[2]
        passwd = sys.argv[3]
        courseid = sys.argv[4]
        destino = sys.argv[5]
        login(username, passwd)
        userid = getuserid()
        if userid == -1:
            print('ERROR! No se ha podido completar el login correctamente. Compruebe la url, el usuario y el password')
        else:
            print('Se ha logueado correctamente. El id del usuario logueado es: '+str(userid))
            core_enrol_get_enrolled_users(courseid)


def login(user, pwd):
    try:
        global sesion
        authdata = {
            'action': 'login',
            'username': user,
            'password': pwd
        }
        with session() as sesion:
            sesion.post(baseurl + 'login/index.php', data=authdata)
    except requests.exceptions.RequestException:
        print('ERROR! No se ha podido establecer la conexión con la URL proporcionada')
        sys.exit()


def getuserid():
    try:
        r = sesion.get(baseurl + 'index.php')
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            temp = soup.findAll("div", {"class": "logininfo"})[0].find('a').attrs['href']
            index = temp.index('id=')
            if index != '-1':
                return int(temp[index + 3:None])
            else:
                return -1
        else:
            return -1
    except ValueError:
        return -1
    except requests.exceptions.RequestException:
        print('ERROR! No se ha podido establecer la conexión con la URL proporcionada')
        sys.exit()


def core_enrol_get_enrolled_users(courseid):
    users = []
    r = sesion.get(baseurl + 'user/index.php?id='+courseid+'&perpage=5000')
    # Le pongo &perpage=5000 por si hay muchos usuarios
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        tablaparticipantes = soup.find("table", {"id": "participants"})
        if tablaparticipantes.contents[1]:
            for unparticipante in tablaparticipantes.contents[1]:
                enlaces = unparticipante.findAll('a')
                for elem in enlaces:
                    if 'href' in elem.attrs:
                        href = elem.attrs['href']
                        if 'user/view.php?id=' in href:
                            user = dict()
                            user['id'] = 0
                            for unparam in href.split('?')[1].split('&'):
                                if 'id' in unparam:
                                    user['id'] = int(unparam.split('=')[1])
                            r = sesion.get(href)
                            soup = BeautifulSoup(r.text, 'html.parser')
                            perfil = soup.find("div", {"class": "userprofile"})

                            # profileimageurl. Podría conseguir la imagen pequeña tambien si cambio f1 por f2
                            profileimageurl = perfil.find("img", {"class": "userpicture"})
                            if 'src' in profileimageurl.attrs:
                                user['profileimageurl'] = profileimageurl.attrs['src'].split('?')[0]
                                user['profileimageurlsmall'] = user['profileimageurl'][:-1]+'2'

                            # fullname
                            fullname = perfil.find("div", {"class": "page-header-headings"})
                            if fullname:
                                user['fullname'] = fullname.text

                            # description
                            description = perfil.find("div", {"class": "description"})
                            if description:
                                user['description'] = description.text

                            # enrolledcourses, firstaccess & lastaccess
                            href = baseurl + 'user/profile.php?id=' + str(user['id'])
                            r = sesion.get(href)
                            soup = BeautifulSoup(r.text, 'html.parser')

                            # enrolledcourses
                            user['enrolledcourses'] = []
                            a = soup.findAll("a")
                            for unA in a:
                                if 'href' in unA.attrs:
                                    href = unA.attrs['href']
                                    patron = 'user/view.php?id=' + str(user['id']) + '&course='
                                    if href and patron in href:
                                        course = dict()
                                        index = href.index('&course=')
                                        course['id'] = int(href[index + 8:None])
                                        course['fullname'] = unA.text
                                        user['enrolledcourses'].append(course)

                            # firstaccess & lastaccess
                            allli = soup.findAll("li", {"class": "contentnode"})
                            for unLi in allli:
                                dt = unLi.find('dt').text
                                dd = unLi.find('dd')
                                if dt and dd:
                                    if 'Primer acceso' in dt or 'First access' in dt or 'Lehen sarrera' in dt:
                                        user['firstaccess'] = dd.text
                                    if 'Last access' in dt or 'Último acceso' in dt or 'Azken sarrera' in dt:
                                        user['lastaccess'] = dd.text

                            # bloque profile_tree
                            user['groups'] = []
                            user['roles'] = []
                            profile_tree = perfil.find("div", {"class": "profile_tree"})
                            if profile_tree:
                                for unaSeccion in profile_tree.contents:
                                    aux = unaSeccion.findAll("li", {"class": "contentnode"})
                                    if aux:
                                        for unLi in aux:
                                            dt = unLi.find('dt').text
                                            dd = unLi.find('dd')
                                            if dt and dd:

                                                # email
                                                if 'Email' in dt or 'Dirección de correo' in dt or 'E-posta' in dt:
                                                    user['email'] = dd.find("a").text

                                                # country
                                                elif 'Country' in dt or 'País' in dt or 'Herrialdea' in dt:
                                                    user['country'] = dd.text

                                                # city
                                                elif 'City' in dt or 'Ciudad' in dt or 'Hiria' in dt:
                                                    user['city'] = dd.text

                                                # Web
                                                elif 'web' in dt.lower():
                                                    user['url'] = dd.find("a").text

                                                # ICQ
                                                elif 'ICQ' in dt:
                                                    user['icq'] = dd.find("a").text

                                                # Skype
                                                elif 'Skype' in dt:
                                                    user['skype'] = dd.find("a").text

                                                # Yahoo
                                                elif 'Yahoo' in dt:
                                                    user['yahoo'] = dd.find("a").text

                                                # AIM
                                                elif 'AIM' in dt:
                                                    user['aim'] = dd.find("a").text

                                                # MSN
                                                elif 'MSN' in dt:
                                                    user['msn'] = dd.text

                                                # groups. En la 3.5 no funciona porque no tiene enlaces
                                                elif 'Group' in dt or 'Grupo' in dt or 'Taldea' in dt:
                                                    for unGrupo in dd.findAll('a'):
                                                        if 'href' in unGrupo.attrs:
                                                            href = unGrupo.attrs['href']
                                                            index = href.index('group=')
                                                            group = dict()
                                                            group['id'] = int(href[index + 6:None])
                                                            group['name'] = unGrupo.text
                                                            user['groups'].append(group)

                                                # roles
                                                elif 'Roles' in dt or 'Rolak' in dt:
                                                    for unRol in dd.findAll('a'):
                                                        if 'href' in unRol.attrs:
                                                            href = unRol.attrs['href']
                                                            index = href.index('roleid=')
                                                            role = dict()
                                                            role['id'] = int(href[index + 7:None])
                                                            role['name'] = unRol.text
                                                            user['roles'].append(role)
                            users.append(user)
                    break  # Hay dos enlaces iguales por cada participante así que despues del primero salimos del bucle
            guardarenarchivojson(users)
        else:
            print('ERROR! El usuario logueado no pertenece a ese curso')
            sys.exit()
    elif r.status_code == 404:
        print('ERROR! No se ha encontrado ninguna tarea con ese id')
        sys.exit()
    else:
        print('ERROR: ' + str(r.status_code) + ' ' + r.reason)
        sys.exit()


def guardarenarchivo(data):
    with open(destino+str(time.time())+'.txt', 'w', encoding='utf8') as f:
        print(data, file=f)


def guardarenarchivojson(data):
    with open(destino+str(time.time())+'.json', 'w', encoding='utf8') as json_file:
        json.dump(data, json_file, ensure_ascii=False)


main()
