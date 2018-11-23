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
        str2 = ' http://localhost/moodle/ profesor2 Profesor2* 5 D:\\resultscraper.json'
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
    r = sesion.get(baseurl + 'user/index.php?id='+courseid)
    # /user/index.php?&id=2&perpage=5000 Si no muestra todos
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        tablaparticipantes = soup.find("table", {"id": "participants"})
        for unparticipante in tablaparticipantes.contents[1]:
            enlaces = unparticipante.findAll('a')
            for elem in enlaces:
                if 'href' in elem.attrs:
                    href = elem.attrs['href']
                    if 'user/view.php?id=' in href:
                        for unparam in href.split('?')[1].split('&'):
                            if 'id' in unparam:
                                id = int(unparam.split('=')[1])
                            elif 'course' in unparam:
                                course = int(unparam.split('=')[1])
                        r = sesion.get(href)
                        soup = BeautifulSoup(r.text, 'html.parser')

                        print('')



        # guardarenarchivo(tablaparticipantes)
        temp = soup.findAll('a')
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
    with open(destino+'.txt', 'w', encoding='utf8') as f:
        print(data, file=f)


def guardarenarchivojson(data):
    with open(destino+str(time.time())+'.json', 'w', encoding='utf8') as json_file:
        json.dump(data, json_file, ensure_ascii=False)


main()
