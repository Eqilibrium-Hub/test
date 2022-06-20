# -*- coding: utf-8 -*-

from odoo import http, exceptions, models, fields, tools
from odoo.http import request
from odoo.http import Response
from odoo.service import security
from odoo.tools import pycompat
from lxml import etree

import hashlib
import base64
import uuid
import re

from datetime import datetime, tzinfo, timedelta
import time
import dateutil.rrule as rrule
from dateutil.tz import tzlocal
import pytz
from ics import Calendar, Event, DisplayAlarm
import io

#Debug
import logging

_logger = logging.getLogger(__name__)

davheader = '1, 2, 3, calendar-access'
baseuri = '/caldav/calendar/'

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text

class UserAgent:
    def __init__(self, agent):
        self.useragent = agent

    def isEvolution(self):
        if self.useragent[:9]=='Evolution':
            return True
        return False
    
    def isiOS(self):
        if self.useragent[:3]=='iOS':
            return True
        return False

    def isMac(self):
        if self.useragent[:3]=='Mac':
            return True
        return False
    
    def isOther(self):
        if not self.isEvolution() and not self.isiOS() and not self.isMac():
            return True
        return False

class OpentechCaldav(http.Controller):
    _inherit = "ir.http"
    
    @http.route(['/.well-known/caldav','/caldav','/caldav/v2','/caldav/<string:username>','/caldav/calendar','/caldav/calendar/<string:username>','/caldav/calendar/<string:username>/<string:ics>'], type="http", auth='none', csrf=False)
    def caldav(self,username='',ics=''):

        calresponse = None

        auth_header = request.httprequest.headers.get('Authorization')

        if not auth_header:
            calresponse = request.make_response('<!DOCTYPE html>\n<html><head><title>Access is denied.</title></head><body><h2><i>Access is denied.</i></h2></body></html>', headers=[('WWW-Authenticate', 'Basic realm="Open Tech Odoo CalDav Support"'),('Content-Type', 'text/html; charset=utf-8'),('Connection', 'close')])
            calresponse.status = '401 Unauthorized'
            return calresponse
            
        else:
            authentication = auth_header.split()
            
            userdata = base64.b64decode(authentication[1]).decode('utf8').split(':')
            
            user = request.env['res.users'].search([('login','=',userdata[0])])
            # res = security.check(request.cr.dbname, userdata[0], userdata[1])
            res = request.session.authenticate(request.cr.dbname, userdata[0], userdata[1])
            
            if not res:
                calresponse = request.make_response('<!DOCTYPE html>\n<html><head><title>Access is denied.</title></head><body><h2><i>Access is denied.</i></h2></body></html>', headers=[('WWW-Authenticate', 'Basic realm="Open Tech Odoo CalDav Support"'),('Content-Type', 'text/html; charset=utf-8')])
                calresponse.status = '401 Unauthorized'
                return calresponse
            
            # if request.httprequest.path == '/.well-known/caldav' or request.httprequest.path == '/.well-known/caldav/' or request.httprequest.path == '/caldav/v2' or request.httprequest.path == '/caldav/v2/':
            #     calresponse = request.make_response('',headers=[('Location', '/caldav')])
            #     calresponse.status = '301 Moved Permanently'
            #     return calresponse
            
            request.uid = res
            
            self.userdata = request.env['res.users'].browse(res)
            
            if request.httprequest.method == 'PROPFIND':
                respuesta = self._propfind(self.userdata)
                return respuesta
            elif request.httprequest.method == 'OPTIONS':
                respuesta = self._options()
                return respuesta
            elif request.httprequest.method == 'REPORT':
                respuesta = self._report(self.userdata)
                return respuesta
            elif request.httprequest.method == 'PUT':
                respuesta = self._put(self.userdata, ics)
                return respuesta
            elif request.httprequest.method == 'DELETE':
                respuesta = self._delete(self.userdata, ics)
                return respuesta
            elif request.httprequest.method == 'GET':
                respuesta = self._get(self.userdata, ics)
                return respuesta
            elif request.httprequest.method == 'PROPPATCH':
                respuesta = self._proppatch(self.userdata)
                return respuesta
            
            calresponse = request.make_response('', headers=[('DAV',davheader)])
            calresponse.status = '404 Not Found'
            respuesta = calresponse
            return respuesta
    
    # ~ ****************************************************************************************************************
    # ~ PROPFIND *********************************************************************************************************    
    
    @classmethod
    def _propfind(self, userdata):
        attributes = [
            'xmlns="DAV:"',
            'xmlns:C="urn:ietf:params:xml:ns:caldav"',
            'xmlns:CR="urn:ietf:params:xml:ns:carddav"',
            'xmlns:CS="http://calendarserver.org/ns/"',
            'xmlns:ICAL="http://apple.com/ns/ical/"',
            'xmlns:ME="http://me.com/_namespace/"',
            'xmlns:RADICALE="http://radicale.org/ns/"'
            ]
        
        xmlresponses = []
        if request.httprequest.path == '/caldav' or request.httprequest.path == '/caldav/' or request.httprequest.path == '/.well-known/caldav' or request.httprequest.path == '/.well-known/caldav/' or request.httprequest.path == '/caldav/v2':
            xmlresponses.append(self._propfind_rutabase(userdata))
        elif request.httprequest.path == '/caldav/calendar' or request.httprequest.path == '/caldav/calendar/':
            xmlresponses = self._propfind_rutauser(userdata)
        if request.httprequest.path == '/caldav/calendar/' + userdata[0].login or request.httprequest.path == '/caldav/calendar/' + userdata[0].login + '/':
            xmlresponses.append(self._propfind_rutacalendario(userdata))
            
        response = ''
        for xmlresponse in xmlresponses:
            response += etree.tostring(xmlresponse).decode('utf-8')
        
        reemplazar = {
            "<calendar": "<C:calendar",
            "</calendar": "</C:calendar",
            "<addressbook-home-set": "<CR:addressbook-home-set",
            "</addressbook-home-set": "</CR:addressbook-home-set",
            "<addressbook-description": "<CR:addressbook-description",
            "</addressbook-description": "</CR:addressbook-description",
            "</getctag": "</CS:getctag",
            "<getctag": "<CS:getctag",
            "<comp ": "<C:comp ",
            "<shared-owner" : "<C:shared-owner",
            "<C:calendar-color" :"<ICAL:calendar-color",
            "</C:calendar-color" :"</ICAL:calendar-color",
            "<C:calendar-order" :"<ICAL:calendar-order",
            "</C:calendar-order" :"</ICAL:calendar-order",
            "<C:calendar-proxy-read-for" :"<CS:calendar-proxy-read-for",
            "</C:calendar-proxy-read-for" :"</CS:calendar-proxy-read-for",
            "<C:calendar-proxy-write-for" :"<CS:calendar-proxy-write-for",
            "</C:calendar-proxy-write-for" :"</CS:calendar-proxy-write-for",
            "<autoprovisioned" :"<ICAL:autoprovisioned",
            "</autoprovisioned" :"</ICAL:autoprovisioned",
            "<language-code" :"<ICAL:language-code",
            "</language-code" :"</ICAL:language-code",
            "<location-code" :"<ICAL:location-code",
            "</location-code" :"</ICAL:location-code",
            "<refreshrate" :"<ICAL:refreshrate",
            "</refreshrate" :"</ICAL:refreshrate",
            "<default-alarm-vevent-date" :"<C:default-alarm-vevent-date",
            "</default-alarm-vevent-date" :"</C:default-alarm-vevent-date",
            "<default-alarm-vevent-datetime" :"<C:default-alarm-vevent-datetime",
            "</default-alarm-vevent-datetime" :"</C:default-alarm-vevent-datetime",
            "<supported-calendar-component-set" :"<C:supported-calendar-component-set",
            "</supported-calendar-component-set" :"</C:supported-calendar-component-set",
            "<dropbox-home-URL" :"<CS:dropbox-home-URL",
            "</dropbox-home-URL" :"</CS:dropbox-home-URL",
            "<email-address-set" :"<CS:email-address-set",
            "</email-address-set" :"</CS:email-address-set",
            "<invite" :"<CS:invite",
            "</invite" :"</CS:invite",
            "<source" :"<CS:source",
            "</source" :"</CS:source",
            "<subscribed-strip-alarms" :"<CS:subscribed-strip-alarms",
            "</subscribed-strip-alarms" :"</CS:subscribed-strip-alarms",
            "<subscribed-strip-attachments" :"<CS:subscribed-strip-attachments",
            "</subscribed-strip-attachments" :"</CS:subscribed-strip-attachments",
            "<subscribed-strip-todos" :"<CS:subscribed-strip-todos",
            "</subscribed-strip-todos" :"</CS:subscribed-strip-todos",
            "<pre-publish-url" :"<CS:pre-publish-url",
            "</pre-publish-url" :"</CS:pre-publish-url",
            "<publish-url" :"<CS:publish-url",
            "</publish-url" :"</CS:publish-url",
            "<publish-transports" :"<CS:publish-transports",
            "</publish-transports" :"</CS:publish-transports",
            "<pushkey" :"<CS:pushkey",
            "</pushkey" :"</CS:pushkey",
            "<max-attendees-per-instance" :"<CR:max-attendees-per-instance",
            "</max-attendees-per-instance" :"</CR:max-attendees-per-instance",
            "<notification-URL" :"<CS:notification-URL",
            "</notification-URL" :"</CS:notification-URL",
            "<allowed-sharing-modes" :"<CS:allowed-sharing-modes",
            "</allowed-sharing-modes" :"</CS:allowed-sharing-modes",
            "<bulk-requests" :"<ME:bulk-requests",
            "</bulk-requests" :"</ME:bulk-requests",
            "<schedule-inbox-URL" :"<C:schedule-inbox-URL",
            "</schedule-inbox-URL" :"</C:schedule-inbox-URL",
            "<schedule-calendar-transp" :"<C:schedule-calendar-transp",
            "</schedule-calendar-transp" :"</C:schedule-calendar-transp",
            "<schedule-default-calendar-URL" :"<C:schedule-default-calendar-URL",
            "</schedule-default-calendar-URL" :"</C:schedule-default-calendar-URL",
            "<schedule-outbox-URL" :"<C:schedule-outbox-URL",
            "</schedule-outbox-URL" :"</C:schedule-outbox-URL",
            "<displayname" :"<RADICALE:displayname",
            "</displayname" :"</RADICALE:displayname"
        }
        response = replace_all(response, reemplazar)

        xmlres = "<?xml version='1.0' encoding='utf-8'?>\n<multistatus " + ' '.join(attributes) + ">" +  response + "</multistatus>"

        self.agent = UserAgent(request.httprequest.headers.get('User-Agent'))

        calresponse = request.make_response(xmlres,headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '207 Multi-Status'
        return calresponse

    @classmethod
    def _propfind_estructura(self, hreforigen=''):
        response = etree.Element('response')
        href = etree.SubElement(response, 'href')
        if hreforigen == '':
            href.text = request.httprequest.path
        else:
            href.text = hreforigen


        propstat = etree.SubElement(response,'propstat')
        prop200 = etree.SubElement(propstat, 'prop')
        status = etree.SubElement(propstat, 'status')
        status.text = 'HTTP/1.1 200 OK'

        return response, prop200
    
    @classmethod
    def _propfind_notfound(self, response, notfound):
        if len(notfound) > 0:
            propstat = etree.SubElement(response, 'propstat')
            prop404 = etree.SubElement(propstat,'prop')
            status = etree.SubElement(propstat,'status')
            status.text = 'HTTP/1.1 404 Not Found'
            for e in notfound:
                etree.SubElement(prop404, e)
        return response
    
    @classmethod
    def _propfind_rutabase(self,userdata):
        response, prop200 = self._propfind_estructura('/caldav/')
        params = etree.fromstring(request.httprequest.data)
        notfound = []

        for propedi in params[0]:
            proped = propedi.tag.split('}')[1]

            # 200 Ok
            if proped == 'resourcetype':
                resourcetype = etree.SubElement(prop200, proped)
                etree.SubElement(resourcetype, 'collection')

            elif proped == 'current-user-principal':
                cup = etree.SubElement(prop200, proped)
                href = etree.SubElement(cup, 'href')
                href.text = baseuri

            # 404 Not Found
            else:
                notfound.append(proped)

        return self._propfind_notfound(response, notfound)

    @classmethod
    def _propfind_rutauser(self,userdata):
        responses = []
        params = etree.fromstring(request.httprequest.data)

        hrefs = [ baseuri ]
        
        listatagsmulti = [
            'resourcetype'
            ]

        multires = False
        for propedi in params[0]:
            if propedi.tag.split('}')[1] in listatagsmulti:
                multires = True
                break
        
        if multires:
            hrefs.append( baseuri + userdata[0].login )

        for href in hrefs:
            response, prop200 = self._propfind_estructura(href)
            notfound = []

            for propedi in params[0]:
                proped = propedi.tag.split('}')[1]

                if href == baseuri:
                    # 200 Ok
                    if proped == 'principal-URL' or proped == 'calendar-home-set' or proped == 'calendar-user-address-set' or proped == 'current-user-principal' or proped == 'owner':
                        cup = etree.SubElement(prop200, proped)
                        nhref = etree.SubElement(cup, 'href')
                        nhref.text = baseuri
                    
                    elif proped == 'resourcetype':
                        cup = etree.SubElement(prop200, proped)
                        etree.SubElement(cup, 'principal')
                        etree.SubElement(cup, 'collection')

                    elif proped == 'principal-collection-set':
                        cup = etree.SubElement(prop200, proped)
                        attr = etree.SubElement(cup, 'href')
                        attr.text='/caldav/'

                    elif proped == 'supported-report-set':
                        
                        listareportset = [ 'expand-property', 'principal-search-property-set', 'principal-property-search']

                        cup = etree.SubElement(prop200,proped)
                        for reportset in listareportset:
                            sr = etree.SubElement(cup, 'supported-report')
                            sr = etree.SubElement(sr, 'report')
                            etree.SubElement(sr, reportset)

                    elif proped == 'current-user-privilege-set':
                        
                        listaprivilegeset = [ 'read', 'all', 'write', 'write-properties', 'write-content']

                        cup = etree.SubElement(prop200,proped)
                        for privilegeset in listaprivilegeset:
                            sr = etree.SubElement(cup, 'privilege')
                            etree.SubElement(sr, privilegeset)

                    # 404 Not Found
                    else:
                        notfound.append(proped)

                elif href == baseuri + userdata[0].login:
                    if proped == 'resourcetype':
                        cup = etree.SubElement(prop200, proped)
                        etree.SubElement(cup, 'calendar')
                        etree.SubElement(cup, 'collection')
                    
                    elif proped == 'supported-calendar-component-set':
                        cup = etree.SubElement(prop200, proped)
                        attr = etree.SubElement(cup, 'comp')
                        attr.set('name', 'VEVENT')
                    
                    elif proped == 'displayname':
                        cup = etree.SubElement(prop200, proped)
                        cup.text = userdata[0].name
                    
                    elif proped == 'getctag' or proped == 'getetag':
                        ctag = etree.SubElement(prop200, proped)
                        calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id)], order='write_date desc')
                        if len(calendar) > 0:
                            ctag.text = '"' + hashlib.sha224(str(calendar[0].write_date).encode('utf-8')).hexdigest() + '"'
                        else:
                            ctag.text = '"' + hashlib.sha224(str(datetime.now().isoformat(' ')).encode('utf-8')).hexdigest() + '"'
                    
                    elif proped == 'getcontenttype':
                        cup = etree.SubElement(prop200, proped)
                        cup.text = 'text/calendar'

                    elif proped == 'calendar-description':
                        cup = etree.SubElement(prop200, proped)
                        cup.text = 'Open Tech Odoo CalDav - ' + userdata[0].name

                    elif proped == 'current-user-privilege-set':
                        
                        listaprivilegeset = [ 'read', 'all', 'write', 'write-properties', 'write-content']

                        cup = etree.SubElement(prop200,proped)
                        for privilegeset in listaprivilegeset:
                            sr = etree.SubElement(cup, 'privilege')
                            etree.SubElement(sr, privilegeset)

                    elif proped == 'owner':
                        cup = etree.SubElement(prop200, proped)
                        attr = etree.SubElement(cup, 'href')
                        attr.text = baseuri

                    elif proped == 'supported-report-set':
                        
                        listareportset = [ 'expand-property', 'principal-search-property-set', 'principal-property-search', 'sync-collection', 'calendar-multiget', 'calendar-query']

                        cup = etree.SubElement(prop200,proped)
                        for reportset in listareportset:
                            sr = etree.SubElement(cup, 'supported-report')
                            sr = etree.SubElement(sr, 'report')
                            etree.SubElement(sr, reportset)
                    
                    elif proped == 'sync-token':
                        calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id)], order='write_date desc', limit=1)
                        callastwrite = str(calendar.write_date).encode('utf-8')

                        synctoken = etree.SubElement(prop200, proped)
                        synctoken.text='https://opentech.es/ns/sync/' + hashlib.sha224(callastwrite).hexdigest()


                    # 404 Not Found
                    else:
                        notfound.append(proped)

            responses.append(self._propfind_notfound(response, notfound))

        return responses

    @classmethod
    def _propfind_rutacalendario(self, userdata):
        response, prop200 = self._propfind_estructura()
        params = etree.fromstring(request.httprequest.data)
        notfound = []

        for propedi in params[0]:
            proped = propedi.tag.split('}')[1]

            # 200 Ok
            if proped == 'getctag':
                ctag = etree.SubElement(prop200, proped)
                calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id)], order='write_date desc')

                if len(calendar) > 0:
                    ctag.text = '"' + hashlib.sha224(str(calendar[0].write_date).encode('utf-8')).hexdigest() + '"'
                else:
                    ctag.text = '"' + hashlib.sha224(str(datetime.now().isoformat(' ')).encode('utf-8')).hexdigest() + '"'
            
            elif proped == 'current-user-privilege-set':
                privileges = [ 'read', 'write', 'write-content', 'all' ]
                privilegeset = etree.SubElement(prop200, proped)
                for p in privileges:
                    privilege = etree.SubElement(privilegeset, 'privilege')
                    etree.SubElement(privilege, p)

            # Thunderbird FIX

            elif proped == 'resourcetype':
                cup = etree.SubElement(prop200, proped)
                etree.SubElement(cup, 'calendar')
                etree.SubElement(cup, 'collection')

            elif proped == 'displayname':
                cup = etree.SubElement(prop200, proped)
                cup.text = userdata[0].name

            elif proped == 'owner':
                cup = etree.SubElement(prop200, proped)
                attr = etree.SubElement(cup, 'href')
                attr.text = baseuri

            elif proped == 'current-user-principal':
                cup = etree.SubElement(prop200, proped)
                href = etree.SubElement(cup, 'href')
                href.text = baseuri

            elif proped == 'supported-report-set':
                
                listareportset = [ 'expand-property', 'principal-search-property-set', 'principal-property-search', 'sync-collection', 'calendar-multiget', 'calendar-query']

                cup = etree.SubElement(prop200,proped)
                for reportset in listareportset:
                    sr = etree.SubElement(cup, 'supported-report')
                    sr = etree.SubElement(sr, 'report')
                    etree.SubElement(sr, reportset)

            elif proped == 'supported-calendar-component-set':
                cup = etree.SubElement(prop200, proped)
                attr = etree.SubElement(cup, 'comp')
                attr.set('name', 'VEVENT')

            # END Thunderbird FIX

            # 404 Not Found
            else:
                notfound.append(proped)

        return self._propfind_notfound(response, notfound)

    # ~ ****************************************************************************************************************
    # ~ OPTIONS
    # *********************************************************************************************************
    
    @classmethod
    def _options(self): 
        calresponse = request.make_response('', headers=[('DAV',davheader),('Allow','DELETE, GET, OPTIONS, PROPFIND, PUT, REPORT')])
        calresponse.status = '200 OK'
        return calresponse
        # Implementado: REPORT, PUT, PROPFIND, OPTIONS, DELETE, GET
    
    # ~ ****************************************************************************************************************
    # ~ DELETE
    # *********************************************************************************************************
    
    @classmethod
    def _delete(self, userdata, ics):
        calevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',ics)])
        calevent.unlink()
        
        res_multistatus = etree.Element('multistatus')
        res_response = etree.SubElement(res_multistatus, 'response')
        res_href = etree.SubElement(res_response, 'href')
        res_href.text = '/caldav/calendar/' + userdata[0].login + '/' + ics
        res_status = etree.SubElement(res_response, 'status')
        res_status.text = 'HTTP/1.1 200 OK'
        
        xmlres = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(res_response,encoding="utf-8").decode("utf-8")
        
        calresponse = request.make_response(xmlres.replace('<multistatus>', '<multistatus xmlns="DAV:">'), headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '200 OK'
        return calresponse
    
    # ~ ****************************************************************************************************************
    # ~ REPORT *********************************************************************************************************

    @classmethod
    def _report(self, userdata):
        params = etree.fromstring(request.httprequest.data)
        tag = params.tag.split('}')
        if tag[1] == 'sync-collection':
            return self._sync_collection(userdata)
        elif tag[1] == 'calendar-multiget':
            return self._calendar_multiget(userdata)
        elif tag[1] == 'calendar-query':
            return self._calendar_query(userdata)

        calresponse = request.make_response('', headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '404 Not Found'
        return calresponse
    
    # ~ ****************************************************************************************************************
    # ~ PUT *********************************************************************************************************

    @classmethod
    def _put(self, userdata, ics):
        # Eliminar Alarmas para evitar que falle
        strcalendar = request.httprequest.data.decode('utf-8')

        salarm = re.search('(BEGIN:VALARM)', strcalendar)
        ealarm = re.search('(END:VALARM)', strcalendar)
        
        while salarm:
            strcalendar = strcalendar[:salarm.start(1)] + strcalendar[ealarm.start(1)+10:]
            salarm = re.search('(BEGIN:VALARM)', strcalendar)
            ealarm = re.search('(END:VALARM)', strcalendar)
        
        # Importar entrada
        ical = Calendar(imports=strcalendar)
        offset = 0

        utc_tz = pytz.timezone('UTC')                

        attendees = self._getattendees(userdata,strcalendar)
        
        if len(ical.events) == 1:
            # ~ event = ical.events[0]
            for event in ical.events:
                # Buscar si existe el evento
                calevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',event.uid + '.ics')], order='start')


                # tsstart = event.begin + timedelta(hours=offset)
                tsstart = utc_tz.normalize(event.begin)

                tsend = None
                
                if event.all_day and self.agent.isEvolution():
                    event.end = event.end - timedelta(days=1)

                if event.all_day and event.begin + timedelta(days=2) <= event.end:
                    tsend = utc_tz.normalize(event.end - timedelta(days=2))
                else:
                    tsend = utc_tz.normalize(event.end)
                    # tsend = event.end + timedelta(hours=offset)
                
                if not calevent:
                    # Creamos el nuevo evento
                    calevent = request.env['calendar.event'].create({
                    'name' : event.name,
                    # ~ 'start' : tsstart.isoformat(' '),
                    # ~ 'stop' : tsend.isoformat(' '),
                    'start' : tsstart.strftime('%Y-%m-%d %H:%M:%S'),
                    'stop' : tsend.strftime('%Y-%m-%d %H:%M:%S'),
                    'ics' : ics,
                    'location' : event.location,
                    'allday' : event.all_day
                    })
                    
                else:
                    if len(calevent) > 1:
                        # Elemento Recurrente sin alteración de elementos
                        # Nos quedamos con el primero (está ordenado por fecha)
                        calevent = calevent[0]
                        #************* Extraemos los exdata **********
                        isremoved = re.search('(?<=EXDATE)\S+', strcalendar)
                        if isremoved:
                            rr_removed = re.findall('(?<=EXDATE)\S+', strcalendar)
                            for i in rr_removed:
                                rr_strid = i.split(':')
                                rr_date = None
                                if rr_strid[1][-1:]== 'Z':
                                    rr_date = datetime.strptime(rr_strid[1],'%Y%m%dT%H%M%SZ')
                                else:
                                    rr_date = datetime.strptime(rr_strid[1],'%Y%m%dT%H%M%S')
                                
                                recurrent_id_orig = str(calevent[0].id).split('-')
                                
                                remove_rrevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('recurrence_id','=',recurrent_id_orig[0]),('recurrent_id_date','=',rr_date.isoformat(' '))])
                                
                                if not remove_rrevent:
                                    remove_rrevent = calevent[0].detach_recurring_event()
                                    remove_rrevent.recurrent_id_date = rr_date.isoformat(' ')

                                remove_rrevent.active = False
                        #*********************************************       
                    else:
                        if tsend.strftime('%Y-%m-%dT%H:%M:%S%z') < calevent.start.strftime('%Y-%m-%dT%H:%M:%S%z'):
                            # ~ calevent.start = tsstart.isoformat(' ')
                            # ~ calevent.stop = tsend.isoformat(' ')
                            calevent.start = tsstart.strftime('%Y-%m-%d %H:%M:%S')
                            calevent.stop = tsend.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            # ~ calevent.stop = tsend.isoformat(' ')
                            # ~ calevent.start = tsstart.isoformat(' ')
                            calevent.stop = tsend.strftime('%Y-%m-%d %H:%M:%S')
                            calevent.start = tsstart.strftime('%Y-%m-%d %H:%M:%S')
                        # Modificación de un evento simple
                    calevent.name = event.name
                    calevent.description = event.description
                    calevent.allday = event.all_day
                
                # Ponemos la localización y la descripción
                calevent.location = event.location

                calevent.partner_ids = attendees
                
                for i in attendees:
                    if i.id != userdata.id:
                        attendee = request.env['calendar.attendee'].search([('partner_id', '=', i.id),('event_id','=',calevent.id)])
                        if not attendee:
                            attendee = request.env['calendar.attendee'].create({
                            'partner_id' : i.id,
                            'email' : i.email,
                            'event_id' : calevent.id
                            })
                
                if event.description != False:
                    calevent.description = event.description
                
                # Extraer RRULE
                sevent = re.search('(BEGIN:VEVENT)', strcalendar)
                eevent = re.search('(END:VEVENT)', strcalendar)
                strevent = strcalendar[sevent.start(1):eevent.start(1)+10]
                strrule = ''
                mrrule = re.search('(?<=RRULE)\S+', strevent)
                
                if mrrule and mrrule.group(0) != '':
                    rrulel = mrrule.group(0).split(':')
                    strrule = rrulel[1]

        
                if not strrule == "":
                    calevent.rrule = strrule
                
                # Extraemos la Alarma
                strcalendar = request.httprequest.data.decode('utf-8')
                stralarm = ''
                calevent.alarm_ids = self._getalarm(strcalendar)

        else:
            #VERIFICACION******************************************************************************************
            # Modificar recurrencia
            strorig = request.httprequest.data.decode('utf-8')
            

            sevent = re.search('(BEGIN:VEVENT)', strorig)
            streventorig = ''
            strevent = ''
            while sevent:
                #Extraer evento original
                eevent = re.search('(END:VEVENT)', strorig)
                streventorig = strorig[sevent.start(1):eevent.start(1)+10]
                strorig = strorig[:sevent.start(1)] + strorig[eevent.start(1)+10:]

                
                #Extraer evento sin alarmas ni modificadores incompatibles con Calendar()
                sevent = re.search('(BEGIN:VEVENT)', strcalendar)
                eevent = re.search('(END:VEVENT)', strcalendar)
                strevent = strcalendar[sevent.start(1):eevent.start(1)+10]
                strcalendar = strcalendar[:sevent.start(1)] + strcalendar[eevent.start(1)+10:]

                #************* RRULE *************************
                strrule = ''
                mrrule = re.search('(?<=RRULE)\S+', streventorig)
                
                if mrrule:
                    rrulel = mrrule.group(0).split(':')
                    strrule = rrulel[1]
                
                #*********************************************
                
                #************* IMPORTACIÓN *******************
                strevent = 'BEGIN:VCALENDAR\nPRODID:Open Tech CalDAV Odoo Support\nVERSION:2.0\n' + strevent + '\nEND:VCALENDAR'
                ical = Calendar(imports=strevent)

                #*********************************************

                #************* INICIO Y FIN ******************
                tsstart = list(ical.events)[0].begin
                tsend = None
                if list(ical.events)[0].all_day and (list(ical.events)[0].begin + timedelta(days=2) <= list(ical.events)[0].end):
                    tsend = list(ical.events)[0].end - timedelta(days=2)
                else:
                    tsend = list(ical.events)[0].end
                #*********************************************

                if mrrule:
                    # Se trata del original, lo actualizamos
                    
                    #************* Buscamos el recurrente original
                    calevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',ics)], order='id')
                    #*********************************************
                    
                    #************* Actualizamos el recurrente original
                    calevent[0].name = list(ical.events)[0].name
                    calevent[0].rrule = strrule
                    calevent[0].description = list(ical.events)[0].description
                    calevent[0].allday = list(ical.events)[0].all_day
    
                    calevent[0].location = list(ical.events)[0].location
                    calevent[0].alarm_ids = self._getalarm(streventorig)                    
                    #*********************************************

                    #************* Extraemos los exdata **********
                    isremoved = re.search('(?<=EXDATE)\S+', strevent)
                    if isremoved:
                        rr_removed = re.findall('(?<=EXDATE)\S+', strevent)
                        for i in rr_removed:
                            rr_strid = i.split(':')
                            rr_date = None
                            if rr_strid[1][-1:]== 'Z':
                                rr_date = datetime.strptime(rr_strid[1],'%Y%m%dT%H%M%SZ')
                            else:
                                rr_date = datetime.strptime(rr_strid[1],'%Y%m%dT%H%M%S')
                            
                            recurrent_id_orig = str(calevent[0].id).split('-')
                            
                            remove_rrevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('recurrence_id','=',recurrent_id_orig[0]),('recurrent_id_date','=',rr_date.isoformat(' '))])
                            
                            if not remove_rrevent:
                                remove_rrevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('recurrence_id','=',recurrent_id_orig[0]),('recurrent_id_date','=',rr_date.isoformat(' ')),('active','=',False)])
                                if not remove_rrevent:
                                    remove_rrevent = calevent[0].detach_recurring_event()
                                    remove_rrevent.recurrent_id_date = rr_date.isoformat(' ')

                            remove_rrevent.active = False
                    #*********************************************

                else:
                    #************* Recurrence-id *****************
                    rid = re.search('(?<=RECURRENCE-ID)\S+', strevent)
                    drid = None
                    if rid:
                        recurrenceid = rid.group(0).split(':')
                        if recurrenceid[1][-1:]== 'Z':
                            drid = datetime.strptime(recurrenceid[1],'%Y%m%dT%H%M%SZ')
                        else:
                            drid = datetime.strptime(recurrenceid[1],'%Y%m%dT%H%M%S')
                    #*********************************************
                    
                    calevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',ics),('recurrence_id','=',False)], order='start')
                    

                    # calevent = calevent.pop()

                    recurrent_id_orig = str(calevent.id).split('-')

                    iscreated = re.search('(CREATED)', streventorig)
                    if iscreated:
                        #************* Separación de un RR************
                        calevent = calevent.detach_recurring_event()
                        calevent.recurrent_id_date = drid.isoformat(' ')
                        #*********************************************
                    else:
                        #************* Modificación de un RR**********
                        calevent = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('recurrence_id','=',recurrent_id_orig[0]),('recurrent_id_date','=',drid.isoformat(' '))], order='id')
                        #*********************************************
                    
                    calevent.name = ical.events[0].name
                    # ~ calevent.rrule = mrrule
                    calevent.description = ical.events[0].description
                    calevent.allday = ical.events[0].all_day
    
                    calevent.location = ical.events[0].location
                    calevent.alarm_ids = self._getalarm(streventorig)

                    for i in attendees:
                        if i.id != userdata.id:
                            attendee = request.env['calendar.attendee'].search([('partner_id', '=', i.id),('event_id','=',calevent.id)])
                            if not attendee:
                                attendee = request.env['calendar.attendee'].create({
                                'partner_id' : i.id,
                                'email' : i.email,
                                'event_id' : calevent.id
                                })

                sevent = re.search('(BEGIN:VEVENT)', strorig)
                
            #FIN VERIFICACION**************************************************************************************

            # Fin del original.... comienza el resto de eventos
        calresponse = request.make_response('', headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '201 Created'
        return calresponse

    # ~ ****************************************************************************************************************
    # ~ GET *********************************************************************************************************
    
    @classmethod
    def _get(self, userdata, ics):
        calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',ics)],order='start')
        
        if calendar:
            """ etag = '"' + hashlib.sha224(str(calendar[0].write_date).encode('utf-8')).hexdigest() + '"' """
            if( len(calendar) > 0 ):
                etag = '"' + hashlib.sha224(str(calendar[0].write_date).encode('utf-8')).hexdigest() + '"'
            else:
                etag = '"' + hashlib.sha224(str(datetime.now().isoformat(' ')).encode('utf-8')).hexdigest() + '"'

            calendarevent = self._getics(userdata, ics)
            content = "\r\n".join(map(lambda x: x.decode('utf-8'), calendarevent.values()))
            # content = self._getics(userdata, ics)
        
            calresponse = request.make_response(content, headers=[('DAV',davheader),('Content-Type', 'text/calendar'),('ETag',etag)])
            calresponse.status = '200 Ok'
            return calresponse
        
        calresponse = request.make_response('', headers=[('DAV',davheader)])
        calresponse.status = '404 Not Found'
        return calresponse
    
    # ~ ****************************************************************************************************************
    # ~ PROPPATCH
    # *********************************************************************************************************
    
    @classmethod
    def _proppatch(self, userdata):
        res_response = etree.Element('response')
        href = etree.SubElement(res_response, 'href')
        href.text = '/caldav/' + userdata[0].login + '/'
        
        propstat = etree.SubElement(res_response, 'propstat')
        prop = etree.SubElement(propstat, 'prop')
        status = etree.SubElement(propstat, 'status')
        status.text = 'HTTP/1.1 200 OK'

        tresourcetype = ''
        tsupportedreportset = ''
        tcalendarcomponetset = ''
        tctag = ''
        # ~ attributes = ''
        attributes = ' xmlns="DAV:"'

        isdav = True
        iscaldavurl = False
        isurn = False
        
        isurncard = False
        
        notvalids = []
        
        params = etree.fromstring(request.httprequest.data)

        for child in params[0][0]:
            tag = child.tag.split('}')
            var = tag[0].split('{')
            
            pre = var[1]
            
            # ~ D:
            if pre=='DAV:' and not isdav:
                attributes += ' xmlns="' + var[1] + '"'
                isdav = True
            
            # ~ CS:
            elif pre[0:4]=='http' and not iscaldavurl:
                attributes += ' xmlns:CS="' + var[1] + '"'
                iscaldavurl = True
            
            # ~ C:
            elif pre=="urn:ietf:params:xml:ns:caldav" and not isurn:
                attributes += ' xmlns:C="' + var[1] + '"'
                isurn = True
                
            elif pre=="urn:ietf:params:xml:ns:carddav" and not isurncard:
                attributes += ' xmlns:CR="' + var[1] + '"'
                isurncard = True

            
            if tag[1] == 'calendar-timezone' or tag[1] == 'default-alarm-vevent-date' or tag[1] == 'calendar-color' or tag[1] == 'default-alarm-vevent-datetime' or tag[1] == 'calendar-order':
                purl = etree.SubElement(prop, tag[1])
                
            else:
                notvalids.append(tag[1])
                            
        if len(notvalids) > 0:
            propstatnv = etree.SubElement(res_response, 'propstat')
            propnv = etree.SubElement(propstatnv, 'prop')
            statusnv = etree.SubElement(propstatnv, 'status')
            statusnv.text = 'HTTP/1.1 404 Not Found'
            
            for nv in notvalids:
                etree.SubElement(propnv, nv)

        xmlres = "<?xml version='1.0' encoding='utf-8'?>\n<multistatus" + attributes + ">" + etree.tostring(res_response,encoding="utf-8").decode("utf-8").replace('default-alarm-vevent-date', 'C:default-alarm-vevent-date').replace('calendar-color','CS:calendar-color') + "</multistatus>"
        
        calresponse = request.make_response(xmlres, headers=[('DAV',davheader)])
        calresponse.status = '207 Multi-Status'
        return calresponse
        
    # ~ ****************************************************************************************************************
    # ~ REPORT *********************************************************************************************************
    
    @classmethod
    def _sync_collection(self, userdata):
        calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id)], order='write_date desc', limit=1)
        callastwrite = str(calendar.write_date).encode('utf-8')
        
        calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id)], order='id desc')
        
        res_response = etree.Element('multistatus')
        res_response.set('xmlns', 'DAV:')
        
        propstatfields = []
        
        params = etree.fromstring(request.httprequest.data)
        
        for child in params:
            tag = child.tag.split('}')
            
            if tag[1] == 'sync-token':
                synctoken = etree.SubElement(res_response, 'sync-token')
                synctoken.text = 'https://opentech.es/ns/sync/' + hashlib.sha224(callastwrite).hexdigest()
            
            elif tag[1] == 'prop':
                for prop in child:
                    tag = prop.tag.split('}')
                    propstatfields.append(tag[1])
                
                lastics = ''
                for event in calendar:
                    if event.ics != lastics:
                        responsepropstat = etree.SubElement(res_response, 'response')
                        href = etree.SubElement(responsepropstat, 'href')
                        
                        if event.ics == False:
                            event.ics = str(uuid.uuid4()) + ".ics"
                        
                        href.text = '/caldav/calendar/' + userdata[0].login + '/' + event.ics
                        
                        propstat = etree.SubElement(responsepropstat, 'propstat')
                        prop = etree.SubElement(propstat, 'prop')
                        rstatus = etree.SubElement(propstat, 'status')
                        rstatus.text='HTTP/1.1 200 OK'
                        for ps in propstatfields:
                            if ps == 'getetag':
                                getetag = etree.SubElement(prop, 'getetag')
                                if event.rrule == False:
                                    getetag.text = '"' + hashlib.sha224(str(event.write_date).encode('utf-8')).hexdigest() + '"'
                                else:
                                    getetag.text = '"' + hashlib.sha224(str(event[0].write_date).encode('utf-8')).hexdigest() + '"'
                            elif ps == 'getcontenttype':
                                getcontenttype = etree.SubElement(prop, 'getcontenttype')
                                getcontenttype.text = 'text/calendar;charset=utf-8;component=VEVENT';
                        lastics = event.ics
        
        xmlres = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(res_response,encoding="utf-8").decode("utf-8")
        
        calresponse = request.make_response(xmlres, headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '207 Multi-Status'
        return calresponse

    @classmethod
    def _calendar_multiget(self, userdata):
        params = etree.fromstring(request.httprequest.data)
        
        res_response = etree.Element('multistatus')
        propfields = []
        props = params.find('{DAV:}prop')
        for prop in props:
            tag = prop.tag.split('}')
            propfields.append(tag[1])
        
        hrefs = params.findall('{DAV:}href')
        for href in hrefs:
            ics = href.text.split('/')
            calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',ics[4])],order='start')
        
            response = etree.SubElement(res_response, 'response')
            res_href = etree.SubElement(response, 'href')
            res_href.text = href.text
            res_propstat = etree.SubElement(response, 'propstat')
            res_prop = etree.SubElement(res_propstat, 'prop')
            for i in propfields:
                if i == 'getetag':
                    etag = etree.SubElement(res_prop, 'getetag')
                    
                    if( len(calendar) > 0 ):
                        etag.text = '"' + hashlib.sha224(str(calendar[0].write_date).encode('utf-8')).hexdigest() + '"'
                    else:
                        etag.text = '"' + hashlib.sha224(str(datetime.now().isoformat(' ')).encode('utf-8')).hexdigest() + '"'
                    
                elif i == 'calendar-data':
                    calendardata = etree.SubElement(res_prop,'calendar-data')
                    calendarevent = self._getics(userdata, ics[4])
                    calendardata.text = "\r\n".join(map(lambda x: x.decode('utf-8'), calendarevent.values()))
                    
            res_status = etree.SubElement(res_propstat, 'status')
            res_status.text = 'HTTP/1.1 200 OK'

        xmlres = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(res_response,encoding="utf-8").decode("utf-8").replace('<multistatus>', '<multistatus xmlns="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">').replace('calendar-data>', 'C:calendar-data>')
        
        calresponse = request.make_response(xmlres, headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '207 Multi-Status'
        return calresponse

    @classmethod
    def _calendar_query(self, userdata):
        res_response = etree.Element('multistatus')
        res_response.set('xmlns', 'DAV:')
        
        propstatfields = []
        
        params = etree.fromstring(request.httprequest.data)
        
        for child in params:
            tag = child.tag.split('}')
            
            if tag[1] == 'prop':
                for prop in child:
                    tag = prop.tag.split('}')
                    propstatfields.append(tag[1])
            
            elif tag[1] == 'filter':
                for ef in child:
                    if ef.attrib['name'] == 'VCALENDAR':
                        for f in ef:
                            if f.attrib['name'] == 'VEVENT':
                                fstart = ''
                                fend = ''
                                for j in f:
                                    t = j.tag.split('}')
                                    if t[1] == 'time-range':
                                        atstart = j.attrib['start']
                                        fstart = atstart[:4] + '-' + atstart[4:6] + '-' + atstart[6:8] + ' ' + atstart[9:11] + ':' + atstart[11:13] + ':' + atstart[13:15]
                                        try:
                                            atend = j.attrib['end']
                                            fend = atend[:4] + '-' + atend[4:6] + '-' + atend[6:8] + ' ' + atend[9:11] + ':' + atend[11:13] + ':' + atend[13:15]
                                        except KeyError:
                                            fend = ''

                                calendar = False
                                if fstart != '' and fend != '':
                                    calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id), ('start', '>=', fstart), ('start', '<=', fend)], order='id desc')
                                else:
                                    calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id)], order='id desc')
                                
                                lastics = ''
                                for event in calendar:
                                    if event.ics != lastics:
                                        responsepropstat = etree.SubElement(res_response, 'response')
                                        href = etree.SubElement(responsepropstat, 'href')
                                        
                                        if event.ics == False:
                                            event.ics = str(uuid.uuid4()) + ".ics"
                                        
                                        href.text = '/caldav/calendar/' + userdata[0].login + '/' + event.ics
                                        
                                        propstat = etree.SubElement(responsepropstat, 'propstat')
                                        prop = etree.SubElement(propstat, 'prop')
                                        rstatus = etree.SubElement(propstat, 'status')
                                        rstatus.text='HTTP/1.1 200 OK'
                                        for ps in propstatfields:
                                            if ps == 'getetag':
                                                getetag = etree.SubElement(prop, 'getetag')
                                                getetag.text = '"' + hashlib.sha224(str(event.write_date).encode('utf-8')).hexdigest() + '"'
                                        lastics = event.ics

        xmlres = "<?xml version='1.0' encoding='utf-8'?>\n" + etree.tostring(res_response,encoding="utf-8").decode("utf-8")
        
        calresponse = request.make_response(xmlres, headers=[('DAV',davheader),('Content-Type', 'text/xml')])
        calresponse.status = '207 Multi-Status'
        return calresponse

    # ~ ****************************************************************************************************************
    # ~ PUT ************************************************************************************************************
    
    @classmethod
    def _getalarm(self, strevent):
        stralarm = ''
        salarm = re.search('(BEGIN:VALARM)', strevent)
        ealarm = re.search('(END:VALARM)', strevent)
        if salarm:
            stralarm = strevent[salarm.start(1):ealarm.start(1)+10]
        if stralarm != '':
            alarms = re.search('(?<=TRIGGER)\S+', stralarm)
            alarmv = alarms.group(0).split(':')
            interval = ''
            duration = ''
            sinterval = alarmv[1][-1:]
            if alarmv[1][2:][0] == 'T':
                duration = alarmv[1][3:-1]
                if sinterval == 'M':
                    interval = 'minutes'
                elif sinterval == 'H':
                    interval = 'hours'
            else:
                duration = alarmv[1][2:-1]
                if sinterval == 'D':
                    interval = 'days'
                elif sinterval == 'W':
                    interval = 'weeks'
            
            if interval == "":
                return False
            alarmsearch = request.env['calendar.alarm'].search([('duration', '=', int(duration)),('interval','=',interval)])
            
            if len(alarmsearch.ids) == 0:
                strinterval = duration
                tduration = int(duration)
                if sinterval == 'M':
                    strinterval += ' Minute(s)'
                elif sinterval == 'H':
                    strinterval += ' Hour(s)'
                    tduration = int(duration) * 60
                elif sinterval == 'D':
                    strinterval += ' Day(s)'
                    tduration = int(duration) * 1440
                elif sinterval == 'W':
                    strinterval += ' Week(s)'
                    tduration = int(duration) * 10080
                
                alarmsearch = request.env['calendar.alarm'].create({
                    'name' : strinterval,
                    'alarm_type' : 'notification',
                    'duration' : duration,
                    'interval' : interval,
                    'duration_minutes' : tduration
                })
            return alarmsearch.ids
        return False

    # ~ ****************************************************************************************************************
    # ~ ICS ************************************************************************************************************
    
    @classmethod
    def _getics(self, userdata, ics):
        calendar = request.env['calendar.event'].search([('partner_ids', '=', userdata[0].partner_id[0].id),('ics','=',ics)],order='start asc')
        
        uuid = ics.split('.')
        
        if calendar:
            
            content = self._get_ics_file(calendar[0])

            if self.agent.isEvolution():
                for n, event in content.items():
                    ical = Calendar(imports=event.decode('utf-8'))
                    m = False
                    for e in ical.events:
                        if e.all_day:
                            m = True
                            e.end = e.end + timedelta(days=1)
                    
                    if m:
                        content[n] = str(ical).encode('utf-8')
            
            return content
        
        return False

    @classmethod
    def _getattendees(self, userdata, vevent):
        states = {
            0: 1,
            1: {
            }
        }
        attendee = []
        attendee.append(userdata.email)
        
        index = 0
        process_ok = False
        
        state = 0
        
        ics = io.StringIO(vevent)
        s = ""
        
        for line in ics.readlines():
            t = line.split("\n")
            
            q = t[0].split("\r")
            
            if s != "" and q[0][0:1] != " ":
                l = s.split(":")
                r = l[0].split(";")
                
                if state == 0:
                    if r[0] == "BEGIN" and l[1] == "VEVENT":
                        # ~ Comienzo del vtodo
                        process_ok = False
                        state = states.get(state)
                elif state == 1:
                    if r[0] == "END" and l[1] == "VEVENT":
                        # ~ Fin vtodo
                        index = index + 1
                        process_ok = True
                        break
                    else:
                        if r[0] == "ATTENDEE":
                            # ~ Campos simples
                            if len(l)>2:
                                if not l[2] in attendee:
                                    attendee.append( l[2] )
                else:
                    if state > 0:
                        _logger.info("Open Tech: Estado no implementado....¿Error en la estructura?")

            if q[0][0:1] != " ":
                s = q[0]
            else:
                s = s + q[0][1:]
        
        if not process_ok:
            del attendee[index]

        attendee_ids = None
        
        attendee_obj = request.env['res.partner'].search([('email', 'in', attendee)])
        
        return attendee_obj

    @classmethod
    def _get_ics_file(self, meetings):
        result = {}
    
        def ics_datetime(idate, allday=False):
            if idate:
                if allday:
                    return idate
                else:
                    return idate.replace(tzinfo=pytz.timezone('UTC'))
            return False

        try:
            import vobject
        except ImportError:
            _logger.warning("The `vobject` Python module is not installed, so iCal file generation is unavailable. Please install the `vobject` Python module")
            return result
    
        for meeting in meetings:
            recurrent = False
            cal = vobject.iCalendar()
            event = cal.add('vevent')
    
            if not meeting.start or not meeting.stop:
                raise UserError(_("First you have to specify the date of the invitation."))
            event.add('created').value = ics_datetime(fields.Datetime.now())
            if not meeting.allday:
                event.add('dtstart').value = ics_datetime(meeting.start, meeting.allday)
                event.add('dtend').value = ics_datetime(meeting.stop, meeting.allday)
            event.add('summary').value = meeting.name
            
            # ~ if meeting.allday:
                # ~ event.add('allday').value = meeting.allday
            if meeting.description:
                event.add('description').value = meeting.description
            if meeting.location:
                event.add('location').value = meeting.location
            if meeting.rrule:
                recurrent=True
                # ~ event.add('rrule').value = meeting.rrule
    
            if meeting.alarm_ids:
                for alarm in meeting.alarm_ids:
                    valarm = event.add('valarm')
                    interval = alarm.interval
                    duration = alarm.duration
                    trigger = valarm.add('TRIGGER')
                    trigger.params['related'] = ["START"]
                    if interval == 'days':
                        delta = timedelta(days=duration)
                    elif interval == 'hours':
                        delta = timedelta(hours=duration)
                    elif interval == 'minutes':
                        delta = timedelta(minutes=duration)
                    trigger.value = delta
                    valarm.add('DESCRIPTION').value = alarm.name or u'Odoo'
            for attendee in meeting.attendee_ids:
                attendee_add = event.add('attendee')
                attendee_add.value = u'MAILTO:' + (attendee.email or u'')
            salida=cal.serialize().encode('utf-8')
            if meeting.allday:
                # if self.agent.isEvolution():
                #     meeting.stop = meeting.stop + timedelta(days=1)
                salida=salida.decode('utf-8')
                salida=salida.replace('BEGIN:VEVENT', 'BEGIN:VEVENT\r\nDTSTART;VALUE=DATE:' + meeting.start.strftime('%Y%m%d')+ '\r\nDTEND;VALUE=DATE:' + meeting.stop.strftime('%Y%m%d') )
                salida=salida.encode('utf-8')
            if recurrent:
                salida=salida.decode('utf-8')
                salida=salida.replace('BEGIN:VEVENT', 'BEGIN:VEVENT\r\nRRULE:' + meeting.rrule)
                salida=salida.encode('utf-8')
            # ~ result[meeting.id] = cal.serialize().encode('utf-8')
            result[meeting.id] = salida

        return result
