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
    # /user/index.php?&id=2&perpage=5000 Si no muestra todos
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
                            userid = 0
                            for unparam in href.split('?')[1].split('&'):
                                if 'id' in unparam:
                                    userid = int(unparam.split('=')[1])
                                    print('Id del participante: '+str(userid))
                                elif 'course' in unparam:
                                    course = int(unparam.split('=')[1])
                                    print('Id del curso: ' + str(course))
                            r = sesion.get(href)
                            soup = BeautifulSoup(r.text, 'html.parser')
                            perfil = soup.find("div", {"class": "userprofile"})

                            # profileimageurl. Podría conseguir la imagen pequeña tambien si cambio f1 por f2
                            profileimageurl = perfil.find("img", {"class": "userpicture"})
                            if 'src' in profileimageurl.attrs:
                                profileimageurl = profileimageurl.attrs['src'].split('?')[0]
                                print('Imagen: ' + profileimageurl)

                            # fullname
                            fullname = perfil.find("div", {"class": "page-header-headings"})
                            if fullname:
                                fullname = fullname.text
                                print('Nombre completo: ' + fullname)

                            # description
                            description = perfil.find("div", {"class": "description"})
                            if description:
                                description = description.text
                                print('Descripción: ' + description)

                            # enrolledcourses, firstaccess & lastaccess
                            if userid != 0:
                                href = baseurl + 'user/profile.php?id=' + str(userid)
                                r = sesion.get(href)
                                soup = BeautifulSoup(r.text, 'html.parser')

                                # enrolledcourses
                                a = soup.findAll("a")
                                for unA in a:
                                    if 'href' in unA.attrs:
                                        href = unA.attrs['href']
                                        patron = 'user/view.php?id=' + str(userid) + '&course='
                                        if href and patron in href:
                                            index = href.index('&course=')
                                            id = int(href[index + 8:None])
                                            fullname = unA.text
                                            print('Un curso:   Id=' + str(id) + '   Fullname='+fullname)

                                # firstaccess & lastaccess
                                allli = soup.findAll("li", {"class": "contentnode"})
                                for unLi in allli:
                                    dt = unLi.find('dt').text
                                    dd = unLi.find('dd')
                                    if dt and dd:
                                        if 'Primer acceso' in dt or 'First access' in dt or 'Lehen sarrera' in dt:
                                            firstaccess = dd.text
                                            print('Primer acceso: '+firstaccess)
                                        if 'Last access' in dt or 'Último acceso' in dt or 'Azken sarrera' in dt:
                                            lastaccess = dd.text
                                            print('Último acceso: '+lastaccess)

                            # bloque profile_tree
                            profile_tree = perfil.find("div", {"class": "profile_tree"})
                            if profile_tree:
                                for unaSeccion in profile_tree.contents:
                                    aux = unaSeccion.findAll("li", {"class": "contentnode"})
                                    if aux:
                                        for unLi in aux:
                                            dt = unLi.find('dt').text
                                            dd = unLi.find('dd')
                                            if dt and dd:

                                                #email
                                                if 'mail' in dt:
                                                    email = dd.find("a").text
                                                    print('Email: ' + email)

                                                # country
                                                elif 'Country' in dt or 'País' in dt or 'Herrialdea' in dt:
                                                    country = dd.text
                                                    print('País: ' + country)

                                                # city
                                                elif 'City' in dt or 'Ciudad' in dt or 'Hiria' in dt:
                                                    city = dd.text
                                                    print('Ciudad: ' + city)

                                                # Web
                                                elif 'web' in dt.lower():
                                                    url = dd.find("a").text
                                                    print('Página web: ' + url)

                                                # ICQ
                                                elif 'ICQ' in dt:
                                                    icq = dd.find("a").text
                                                    print('Número de ICQ: ' + icq)

                                                # Skype
                                                elif 'Skype' in dt:
                                                    skype = dd.find("a").text
                                                    print('ID Skype: ' + skype)

                                                # Yahoo
                                                elif 'Yahoo' in dt:
                                                    yahoo = dd.find("a").text
                                                    print('ID Yahoo: ' + yahoo)

                                                # AIM
                                                elif 'AIM' in dt:
                                                    aim = dd.find("a").text
                                                    print('ID AIM: ' + aim)

                                                # MSN
                                                elif 'MSN' in dt:
                                                    msn = dd.text
                                                    print('ID MSN: ' + msn)

                                                # groups
                                                elif 'Group' in dt or 'Grupo' in dt or 'Taldea' in dt:
                                                    for unGrupo in dd.findAll('a'):
                                                        if 'href' in unGrupo.attrs:
                                                            href = unGrupo.attrs['href']
                                                            index = href.index('group=')
                                                            id = int(href[index + 6:None])
                                                            name = unGrupo.text
                                                            print('Un grupo. Id: ' + str(id) + '   Nombre: ' + name)

                                                # roles
                                                elif 'Roles' in dt or 'Rolak' in dt:
                                                    for unRol in dd.findAll('a'):
                                                        if 'href' in unRol.attrs:
                                                            href = unRol.attrs['href']
                                                            index = href.index('roleid=')
                                                            id = int(href[index + 7:None])
                                                            name = unRol.text
                                                            print('Un rol. Id: ' + str(id) + '   Nombre: ' + name)

                            # guardarenarchivo(perfil)
                            print('')
                        break
        else:
            print('ERROR! El usuario logueado no pertenece a ese curso')
            sys.exit()
        # guardarenarchivo(tablaparticipantes)
        # temp = soup.findAll('a')
        # href = ''
        # for elem in temp:
        #     if 'href' in elem.attrs:
        #         href = elem.attrs['href']
        #         if 'grade/grading/manage.php?areaid=' in href:
        #             index = href.index('areaid=')
        #             areas['definitions']['id'] = int(href[index + 7:None])
        #             break
        # if 'grade/grading/manage.php?areaid=' in href:
        #     r = sesion.get(href)
        #     soup = BeautifulSoup(r.text, 'html.parser')
        #     # areas['definitions']['method'] = 'rubric'
        #     areas['definitions']['name'] = soup.findAll("h3", {"class": "definition-name"})[0].contents[0]
        #     tablacriterios = soup.find("table", {"id": "rubric-criteria"})
        #     areas['definitions']['rubric-criteria'] = []
        #     for uncriterio in tablacriterios.contents:
        #         criteria = dict()
        #         criteria['id'] = int(uncriterio.attrs['id'][16:None])
        #         criteria['description'] = uncriterio.contents[0].text
        #         criteria['levels'] = []
        #         for unnivel in uncriterio.contents[1].contents[0].contents[0].contents:
        #             level = dict()
        #             a = unnivel.attrs['id'].split("-")
        #             level['id'] = int(a[len(a)-1])
        #             level['score'] = int(unnivel.find("span", {"class": "scorevalue"}).text)
        #             level['definition'] = unnivel.find("div", {"class": "definition"}).text
        #             criteria['levels'].append(level)
        #         areas['definitions']['rubric-criteria'].append(criteria)
        #     guardarenarchivojson(areas)
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
