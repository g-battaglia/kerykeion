#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This file is part of kerykeion project. For information search
for kerykeion in github.
A big part of this packege is based on Openastro.
"""
#basics
import math, os.path, datetime, pytz, json

#template processing
from string import Template

#minidom parser
from xml.dom.minidom import parseString

#debug
DEBUG = False

#directories
DATADIR = os.path.dirname(__file__)



#calculation and svg drawing class
class SvgInstance:

    """ 
    Creates the instance from which the svg will be generated, it also has some
    astrological information from the module kerykeion.
    Args: name, year, month, day, hours, minuts, city, initial of the nation
    (ex: IT) 
    """

    def __init__(self, kerykeion_objcet):
        dprint("-------------------------------")
        dprint('Birthchart SVG aka KerykeionSVG\n')
        dprint("-------------------------------")  

        # Set output directory.
        self.set_dir = os.path.expanduser("~")

        # Kerykeion instance
        self.user = kerykeion_objcet
        
        try:
            self.user.sun
        except:
            self.user.get_all()

        # Open files:
        
        mainset = os.path.join(DATADIR, "label.json")
        with open(mainset, "r") as settings:
            self.label = json.load(settings)

        colorset = os.path.join(DATADIR, "colors.json")
        with open(colorset, "r") as settings:
            self.colors = json.load(settings)

        aspset = os.path.join(DATADIR, "settingsAspect.json")
        with open(aspset, "r") as settings:
            self.aspects = json.load(settings) 

        planset = os.path.join(DATADIR, "settingsPlanet.json")
        with open(planset, "r") as settings:
            self.planets_asp = json.load(settings)



        # Make a list for the absolute degrees of the points of the graphic.
        
        self.points_deg_ut = self.user.planets_degs + [self.user.houses_degree_ut[0],
         self.user.houses_degree_ut[9], self.user.houses_degree_ut[6],
          self.user.houses_degree_ut[3]]
        
        # Make a list of the relative degrees of the points in the graphic.
        
        self.points_deg = []
        for planet in self.user.planets_list:
            self.points_deg.append(planet["pos"])
        
        self.points_deg = self.points_deg + [self.user.house_list[0]["pos"],
         self.user.house_list[9]["pos"], self.user.house_list[6]["pos"],
         self.user.house_list[3]["pos"]]

        # Make list of the poits sign.

        self.points_sign = []

        for planet in self.user.planets_list:
            self.points_sign.append(planet["sign_num"])
        
        self.points_sign = self.points_sign + [self.user.house_list[0]["sign_num"],
         self.user.house_list[9]["sign_num"], self.user.house_list[6]["sign_num"],
         self.user.house_list[3]["sign_num"]]

        # Make a list of poits if they are retrograde or not.

        self.points_retrograde = []

        for planet in self.user.planets_list:
            self.points_retrograde.append(planet["retrograde"])
        
        self.points_retrograde = self.points_retrograde + [False,
         False, False, False]

        # Makes the sign number list.

        self.houses_sign_graph = []
        for h in self.user.house_list:
            self.houses_sign_graph.append(h['sign_num'])

        
        #screen size       
        self.screen_width = 1200
        self.screen_height = 800


        
        #check for home
        self.home_location = self.user.city
        self.home_geolat = self.user.city_lat
        self.home_geolon = self.user.city_long
        self.home_countrycode =  self.user.country_code
        self.home_timezonestr = self.user.city_tz
        dprint('known home location: %s %s %s' % (self.home_location, self.home_geolat, self.home_geolon))
            
        #default location
        self.location=self.home_location
        self.geolat=float(self.home_geolat)
        self.geolon=float(self.home_geolon)
        self.countrycode=self.home_countrycode
        self.timezonestr=self.home_timezonestr
        
        #current datetime
        now = datetime.datetime.now()

        #aware datetime object
        dt_input = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
        dt = pytz.timezone(self.timezonestr).localize(dt_input)
        
        #naive utc datetime object
        dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()

        #Default
        self.name = self.user.name
        self.charttype = "Natal"
        self.year = self.user.utc.year
        self.month = self.user.utc.month
        self.day = self.user.utc.day
        self.hour = self.user.utc.hour + self.user.utc.minute/100
        self.timezone = self.offsetToTz(dt.utcoffset())
        self.altitude = 25
        self.geonameid = None

        
        #configuration
        #ZOOM 1 = 100%
        self.zoom=1
        
        

        #12 zodiacs
        self.zodiac = ['aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces']
        self.zodiac_short = ['Ari','Tau','Gem','Cnc','Leo','Vir','Lib','Sco','Sgr','Cap','Aqr','Psc']
        self.zodiac_color = ['#482900','#6b3d00','#5995e7','#2b4972','#c54100','#2b286f','#69acf1','#ffd237','#ff7200','#863c00','#4f0377','#6cbfff']
        self.zodiac_element = ['fire','earth','air','water','fire','earth','air','water','fire','earth','air','water']
        
        return
    
    def makeSVG(self):
        """ 
        Generates the SVG file.
        """
        self.SVGname = self.name
        self.type = "Natal"
        #empty element points
        self.fire=0.0
        self.earth=0.0
        self.air=0.0
        self.water=0.0


        #grab normal module data
        self.planets_sign = self.points_sign                            # DONE
        self.planets_degree = self.points_deg                           # DONE
        self.planets_degree_ut = self.points_deg_ut                     # DONE
        self.planets_retrograde = self.points_retrograde                # DONE
        self.houses_degree = self.user.houses_degree                    # DONE
        self.houses_sign = self.houses_sign_graph                       # DONE
        self.houses_degree_ut = self.user.houses_degree_ut              # DONE
        self.lunar_phase = self.user.lunar_phase                        # DONE
        #
        
        #width and height from screen
        ratio = float(self.screen_width) / float(self.screen_height)
        if ratio < 1.3: #1280x1024
            wm_off = 130
        else: # 1024x768, 800x600, 1280x800, 1680x1050
            wm_off = 100
            
        #Settings where once "check for printer"

        svgHeight=self.screen_height-wm_off
        svgWidth=self.screen_width-5.0
        rotate = "0"
        translate = "0"
        viewbox = '0 0 772.2 546.0' #297mm * 2.6 + 210mm * 2.6

            
        
        #template dictionary        
        td = dict()
        r = 240                
        self.c1=0
        self.c2=36
        self.c3=120

        # Start templating

        td['chartname'] = self.SVGname
    
        td['transitRing']=""
        td['degreeRing']=self.degreeRing( r )
        #circles
        td['c1'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c1) + '"'
        td['c1style'] = 'fill: none; stroke: %s; stroke-width: 1px; '%(self.colors['zodiac_radix_ring_2'])
        td['c2'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c2) + '"'
        td['c2style'] = 'fill: %s; fill-opacity:.2; stroke: %s; stroke-opacity:.4; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_radix_ring_1'])
        td['c3'] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r-self.c3) + '"'
        td['c3style'] = 'fill: %s; fill-opacity:.8; stroke: %s; stroke-width: 1px'%(self.colors['paper_1'],self.colors['zodiac_radix_ring_0'])
        td['makeAspects'] = self.makeAspects( r , (r-self.c3))
        td['makeAspectGrid'] = self.makeAspectGrid( r )
        td['makePatterns'] = self.makePatterns()

        td['circleX'] = str(0)
        td['circleY'] = str(0)
        td['svgWidth'] = str(svgWidth)
        td['svgHeight'] = str(svgHeight)
        td['viewbox'] = viewbox
        td['stringTitle'] = self.name
        
        # Tipo di carta   
        self.subtitle = "Personal information:"
        td['stringName'] = self.subtitle
        
        #bottom left


        td['bottomLeft1']= ''
        td['bottomLeft2']= ''
        td['bottomLeft3'] = '%s: %s' % ( ("Lunar Phase"),self.dec2deg(self.lunar_phase['degrees_between_s_m']))
        td['bottomLeft4'] = ''
    
        #lunar phase
        deg = self.lunar_phase['degrees_between_s_m']

        if(deg<90.0):
            maxr=deg
            if(deg>80.0): maxr=maxr*maxr
            lfcx=20.0+(deg/90.0)*(maxr+10.0)
            lfr=10.0+(deg/90.0)*maxr
            lffg,lfbg=self.colors["lunar_phase_0"],self.colors["lunar_phase_1"]

        elif(deg<180.0):
            maxr=180.0-deg
            if(deg<100.0): maxr=maxr*maxr
            lfcx=20.0+((deg-90.0)/90.0*(maxr+10.0))-(maxr+10.0)
            lfr=10.0+maxr-((deg-90.0)/90.0*maxr)
            lffg,lfbg=self.colors["lunar_phase_1"],self.colors["lunar_phase_0"]

        elif(deg<270.0):
            maxr=deg-180.0
            if(deg>260.0): maxr=maxr*maxr
            lfcx=20.0+((deg-180.0)/90.0*(maxr+10.0))
            lfr=10.0+((deg-180.0)/90.0*maxr)
            lffg,lfbg=self.colors["lunar_phase_1"],self.colors["lunar_phase_0"]

        elif(deg<361):
            maxr=360.0-deg
            if(deg<280.0): maxr=maxr*maxr
            lfcx=20.0+((deg-270.0)/90.0*(maxr+10.0))-(maxr+10.0)
            lfr=10.0+maxr-((deg-270.0)/90.0*maxr)
            lffg,lfbg=self.colors["lunar_phase_0"],self.colors["lunar_phase_1"]

        td['lunar_phase_fg'] = lffg        
        td['lunar_phase_bg'] = lfbg
        td['lunar_phase_cx'] = lfcx
        td['lunar_phase_r'] = lfr
        td['lunar_phase_outline'] = self.colors["lunar_phase_2"]

        #rotation based on latitude
        td['lunar_phase_rotate'] = (-90.0-self.geolat)

        #stringlocation
        if len(self.location) > 35:
            split=self.location.split(",")
            if len(split) > 1:
                td['stringLocation']=split[0]+", "+split[-1]
                if len(td['stringLocation']) > 35:
                    td['stringLocation'] = td['stringLocation'][:35]+"..."
            else:
                td['stringLocation']=self.location[:35]+"..."
        else:
            td['stringLocation']=self.location
            
        td['stringDateTime']= str(self.user.year)+'-%(#1)02d-%(#2)02d %(#3)02d:%(#4)02d:%(#5)02d' % {'#1':self.user.month,'#2':self.user.day,'#3':self.user.hours,'#4':self.user.minuts,'#5':00} + self.decTzStr(self.timezone)
        td['stringLat']="%s: %s" %(self.label['latitude'],self.lat2str(self.geolat))
        td['stringLon']="%s: %s" %(self.label['longitude'],self.lon2str(self.geolon))
        

        # Set a detail string:
        self.detail = "Detail"
        td['stringPosition']= self.detail

        #paper_color_X
        td['paper_color_0']=self.colors["paper_0"]
        td['paper_color_1']=self.colors["paper_1"]
        
        
        #planets_color_X
        for i in range(len(self.planets_asp)):
            td['planets_color_%s'%(i)]=self.colors["planet_%s"%(i)]
        
        #zodiac_color_X
        for i in range(12):
            td['zodiac_color_%s'%(i)]=self.colors["zodiac_icon_%s" %(i)]
        
        #orb_color_X
        for i in range(len(self.aspects)):
            td['orb_color_%s'%(self.aspects[i]['degree'])]=self.colors["aspect_%s" %(self.aspects[i]['degree'])]
        
        #config
        td['cfgZoom']=str(self.zoom)
        td['cfgRotate']=rotate
        td['cfgTranslate']=translate
        
        #functions
        td['makeZodiac'] = self.makeZodiac( r )
        td['makeHouses'] = self.makeHouses( r )
        td['makePlanets'] = self.makePlanets( r )
        td['makeElements'] = self.makeElements( r )
        td['makePlanetGrid'] = self.makePlanetGrid()
        td['makeHousesGrid'] = self.makeHousesGrid()
        

        # Read template

        self.xml_svg = os.path.join(DATADIR, 'kerykeionSVG-svg.xml')
        with open(self.xml_svg, "r") as f:
            template = Template(f.read()).substitute(td)
        
        #Write template and create chart file

        self.chartname = os.path.join(self.set_dir, f'{self.name}Chart.svg')
        with open(self.chartname,"w") as f:
            dprint("Creating SVG: lat = "+str(self.geolat)+' lon = '+str(self.geolon)+' loc = '+self.location) 
            f.write(template)

        
        print("SVG generated successfully!")
        return 

    #draw transit ring
    def transitRing(self, r ):
        out = '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: %s; stroke-width: 36px; stroke-opacity: .4;"/>' % (r,r,r-18,self.colors['paper_1'])
        out += '<circle cx="%s" cy="%s" r="%s" style="fill: none; stroke: %s; stroke-width: 1px; stroke-opacity: .6;"/>' % (r,r,r,self.colors['zodiac_transit_ring_3'])
        return out    
    
    #draw degree ring
    def degreeRing( self , r ):
        out=''
        for i in range(72):
            offset = float(i*5) - self.houses_degree_ut[6]
            if offset < 0:
                offset = offset + 360.0
            elif offset > 360:
                offset = offset - 360.0
            x1 = self.sliceToX( 0 , r-self.c1 , offset ) + self.c1
            y1 = self.sliceToY( 0 , r-self.c1 , offset ) + self.c1
            x2 = self.sliceToX( 0 , r+2-self.c1 , offset ) - 2 + self.c1
            y2 = self.sliceToY( 0 , r+2-self.c1 , offset ) - 2 + self.c1
            out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: %s; stroke-width: 1px; stroke-opacity:.9;"/>\n' % (
                x1,y1,x2,y2,self.colors['paper_0'] )
        return out
        
    def degreeTransitRing( self , r ):
        out=''
        for i in range(72):
            offset = float(i*5) - self.houses_degree_ut[6]
            if offset < 0:
                offset = offset + 360.0
            elif offset > 360:
                offset = offset - 360.0
            x1 = self.sliceToX( 0 , r , offset )
            y1 = self.sliceToY( 0 , r , offset )
            x2 = self.sliceToX( 0 , r+2 , offset ) - 2
            y2 = self.sliceToY( 0 , r+2 , offset ) - 2
            out += '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>\n' % (
                x1,y1,x2,y2 )
        return out
    
    #floating latitude an longitude to string
    def lat2str( self, coord ):
        sign=self.label["north"]
        if coord < 0.0:
            sign=self.label["south"]
            coord = abs(coord)
        deg = int(coord)
        min = int( (float(coord) - deg) * 60 )
        sec = int( round( float( ( (float(coord) - deg) * 60 ) - min) * 60.0 ) )
        return "%s°%s'%s\" %s" % (deg,min,sec,sign)
        
    def lon2str( self, coord ):
        sign=self.label["east"]
        if coord < 0.0:
            sign=self.label["west"]
            coord = abs(coord)
        deg = int(coord)
        min = int( (float(coord) - deg) * 60 )
        sec = int( round( float( ( (float(coord) - deg) * 60 ) - min) * 60.0 ) )
        return "%s°%s'%s\" %s" % (deg,min,sec,sign)
    
    #decimal hour to minutes and seconds
    def decHour( self , input ):
        hours=int(input)
        mands=(input-hours)*60.0
        mands=round(mands,5)
        minutes=int(mands)
        seconds=int(round((mands-minutes)*60))
        return [hours,minutes,seconds]
        
    #join hour, minutes, seconds, timezone integere to hour float
    def decHourJoin( self , inH , inM , inS ):
        dh = float(inH)
        dm = float(inM)/60
        ds = float(inS)/3600
        output = dh + dm + ds
        return output

    #Datetime offset to float in hours    
    def offsetToTz( self, dtoffset ):
        dh = float(dtoffset.days * 24)
        sh = float(dtoffset.seconds / 3600.0)
        output = dh + sh
        return output
    
    
    #decimal timezone string
    def decTzStr( self, tz ):
        if tz > 0:
            h = int(tz)
            m = int((float(tz)-float(h))*float(60))
            return " [+%(#1)02d:%(#2)02d]" % {'#1':h,'#2':m}
        else:
            h = int(tz)
            m = int((float(tz)-float(h))*float(60))/-1
            return " [-%(#1)02d:%(#2)02d]" % {'#1':h/-1,'#2':m}

    #degree difference
    def degreeDiff(self, a, b):
        out = float()
        if a > b:
            out = a - b
        if a < b:
            out=b-a
        if out > 180.0:
            out=360.0-out
        return out

    #decimal to degrees (a°b'c")
    def dec2deg( self , dec , type="3"):
        dec=float(dec)
        a=int(dec)
        a_new=(dec-float(a)) * 60.0
        b_rounded = int(round(a_new))
        b=int(a_new)
        c=int(round((a_new-float(b))*60.0))
        if type=="3":
            out = '%(#1)02d&#176;%(#2)02d&#39;%(#3)02d&#34;' % {'#1':a,'#2':b, '#3':c}
        elif type=="2":
            out = '%(#1)02d&#176;%(#2)02d&#39;' % {'#1':a,'#2':b_rounded}
        elif type=="1":
            out = '%(#1)02d&#176;' % {'#1':a}
        return str(out)
    
    #draw svg aspects: ring, aspect ring, degreeA degreeB
    def drawAspect( self , r , ar , degA , degB , color):
            offset = (int(self.houses_degree_ut[6]) / -1) + int(degA)
            x1 = self.sliceToX( 0 , ar , offset ) + (r-ar)
            y1 = self.sliceToY( 0 , ar , offset ) + (r-ar)
            offset = (int(self.houses_degree_ut[6]) / -1) + int(degB)
            x2 = self.sliceToX( 0 , ar , offset ) + (r-ar)
            y2 = self.sliceToY( 0 , ar , offset ) + (r-ar)
            out = '            <line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+color+'; stroke-width: 1; stroke-opacity: .9;"/>\n'
            return out
    
    def sliceToX( self , slice , r, offset):
        plus = (math.pi * offset) / 180
        radial = ((math.pi/6) * slice) + plus
        return r * (math.cos(radial)+1)
    
    def sliceToY( self , slice , r, offset):
        plus = (math.pi * offset) / 180
        radial = ((math.pi/6) * slice) + plus
        return r * ((math.sin(radial)/-1)+1)
    
    def zodiacSlice( self , num , r , style,  type):
        #pie slices
        offset = 360 - self.houses_degree_ut[6]
        #check transit

        dropin=self.c1        
        slice = '<path d="M' + str(r) + ',' + str(r) + ' L' + str(dropin + self.sliceToX(num,r-dropin,offset)) + ',' + str( dropin + self.sliceToY(num,r-dropin,offset)) + ' A' + str(r-dropin) + ',' + str(r-dropin) + ' 0 0,0 ' + str(dropin + self.sliceToX(num+1,r-dropin,offset)) + ',' + str(dropin + self.sliceToY(num+1,r-dropin,offset)) + ' z" style="' + style + '"/>'
        #symbols
        offset = offset + 15
        #check transit
        dropin=18+self.c1
        sign = '<g transform="translate(-16,-16)"><use x="' + str(dropin + self.sliceToX(num,r-dropin,offset)) + '" y="' + str(dropin + self.sliceToY(num,r-dropin,offset)) + '" xlink:href="#' + type + '" /></g>\n'
        return slice + '\n' + sign
    
    def makeZodiac( self , r ):
        output = ""
        for i in range(len(self.zodiac)):
            output = output + self.zodiacSlice( i , r , "fill:" + self.colors["zodiac_bg_%s"%(i)] + "; fill-opacity: 0.5;" , self.zodiac[i]) + '\n'
        return output
        
    def makeHouses( self , r ):
        path = ""

        xr = 12
        for i in range(xr):
            #check transit

            dropin=self.c3
            roff=self.c1
                
            #offset is negative desc houses_degree_ut[6]
            offset = (int(self.houses_degree_ut[int(xr/2)]) / -1) + int(self.houses_degree_ut[i])
            x1 = self.sliceToX( 0 , (r-dropin) , offset ) + dropin
            y1 = self.sliceToY( 0 , (r-dropin) , offset ) + dropin
            x2 = self.sliceToX( 0 , r-roff , offset ) + roff
            y2 = self.sliceToY( 0 , r-roff , offset ) + roff
            
            if i < (xr-1):        
                text_offset = offset + int(self.degreeDiff( self.houses_degree_ut[(i+1)], self.houses_degree_ut[i] ) / 2 )
            else:
                text_offset = offset + int(self.degreeDiff( self.houses_degree_ut[0], self.houses_degree_ut[(xr-1)] ) / 2 )

            #mc, asc, dsc, ic
            if i == 0:
                linecolor=self.planets_asp[12]['color']
            elif i == 9:
                linecolor=self.planets_asp[13]['color']    
            elif i == 6:
                linecolor=self.planets_asp[14]['color']
            elif i == 3:
                linecolor=self.planets_asp[15]['color']
            else:
                linecolor=self.colors['houses_radix_line']

            ############

            dropin=48
                
            xtext = self.sliceToX( 0 , (r-dropin) , text_offset ) + dropin #was 132
            ytext = self.sliceToY( 0 , (r-dropin) , text_offset ) + dropin #was 132
            path = path + '<line x1="'+str(x1)+'" y1="'+str(y1)+'" x2="'+str(x2)+'" y2="'+str(y2)+'" style="stroke: '+linecolor+'; stroke-width: 2px; stroke-dasharray:3,2; stroke-opacity:.4;"/>\n'
            path = path + '<text style="fill: #f00; fill-opacity: .6; font-size: 14px"><tspan x="'+str(xtext-3)+'" y="'+str(ytext+3)+'">'+str(i+1)+'</tspan></text>\n'
                        
        return path
    
    def makePlanets( self , r ):
        
        planets_degut={}
        
        diff=range(len(self.planets_asp))
        for i in range(len(self.planets_asp)):
            if self.planets_asp[i]['visible'] == 1:
                #list of planets sorted by degree                
                planets_degut[self.planets_degree_ut[i]]=i
            
            #element: get extra points if planet is in own zodiac
            pz = self.planets_asp[i]['zodiac_relation']
            cz = self.planets_sign[i]
            extrapoints = 0
            if pz != -1:
                for e in range(len(pz.split(','))):
                    if int(pz.split(',')[e]) == int(cz):
                        extrapoints = 10

            #calculate element points for all planets
            ele = self.zodiac_element[self.planets_sign[i]]            
            if ele == "fire":
                self.fire = self.fire + self.planets_asp[i]['element_points'] + extrapoints
            elif ele == "earth":
                self.earth = self.earth + self.planets_asp[i]['element_points'] + extrapoints
            elif ele == "air":
                self.air = self.air + self.planets_asp[i]['element_points'] + extrapoints
            elif ele == "water":
                self.water = self.water + self.planets_asp[i]['element_points'] + extrapoints
                
        output = ""    
        keys = list(planets_degut.keys())
        keys.sort()
        switch=0
        
        planets_degrouped = {}
        groups = []
        planets_by_pos = list(range(len(planets_degut)))
        planet_drange = 3.4
        #get groups closely together
        group_open=False
        for e in range(len(keys)):
            i=planets_degut[keys[e]]
            #get distances between planets
            if e == 0:
                prev = self.planets_degree_ut[planets_degut[keys[-1]]]
                next = self.planets_degree_ut[planets_degut[keys[1]]]
            elif e == (len(keys)-1):
                prev = self.planets_degree_ut[planets_degut[keys[e-1]]]
                next = self.planets_degree_ut[planets_degut[keys[0]]]    
            else:
                prev = self.planets_degree_ut[planets_degut[keys[e-1]]]
                next = self.planets_degree_ut[planets_degut[keys[e+1]]]
            diffa=self.degreeDiff(prev,self.planets_degree_ut[i])
            diffb=self.degreeDiff(next,self.planets_degree_ut[i])
            planets_by_pos[e]=[i,diffa,diffb]
            #print "%s %s %s" % (self.planets_asp[i]['label'],diffa,diffb)
            if (diffb < planet_drange):
                if group_open:
                    groups[-1].append([e,diffa,diffb,self.planets_asp[planets_degut[keys[e]]]["label"]])
                else:
                    group_open=True
                    groups.append([])
                    groups[-1].append([e,diffa,diffb,self.planets_asp[planets_degut[keys[e]]]["label"]])
            else:
                if group_open:
                    groups[-1].append([e,diffa,diffb,self.planets_asp[planets_degut[keys[e]]]["label"]])                
                group_open=False    
        
        def zero(x): return 0
        planets_delta = list(map(zero,range(len(self.planets_asp))))

        #print groups
        #print planets_by_pos
        for a in range(len(groups)):
            #Two grouped planets            
            if len(groups[a]) == 2:
                next_to_a = groups[a][0][0]-1
                if groups[a][1][0] == (len(planets_by_pos)-1):
                    next_to_b = 0
                else:
                    next_to_b = groups[a][1][0]+1
                #if both planets have room
                if (groups[a][0][1] > (2*planet_drange))&(groups[a][1][2] > (2*planet_drange)):
                    planets_delta[groups[a][0][0]]=-(planet_drange-groups[a][0][2])/2
                    planets_delta[groups[a][1][0]]=+(planet_drange-groups[a][0][2])/2
                #if planet a has room
                elif (groups[a][0][1] > (2*planet_drange)):
                    planets_delta[groups[a][0][0]]=-planet_drange
                #if planet b has room
                elif (groups[a][1][2] > (2*planet_drange)):
                    planets_delta[groups[a][1][0]]=+planet_drange
                
                #if planets next to a and b have room move them
                elif (planets_by_pos[next_to_a][1] > (2.4*planet_drange))&(planets_by_pos[next_to_b][2] > (2.4*planet_drange)):
                    planets_delta[(next_to_a)]=(groups[a][0][1]-planet_drange*2)
                    planets_delta[groups[a][0][0]]=-planet_drange*.5                
                    planets_delta[next_to_b]=-(groups[a][1][2]-planet_drange*2)
                    planets_delta[groups[a][1][0]]=+planet_drange*.5    
                    
                #if planet next to a has room move them
                elif (planets_by_pos[next_to_a][1] > (2*planet_drange)):
                    planets_delta[(next_to_a)]=(groups[a][0][1]-planet_drange*2.5)
                    planets_delta[groups[a][0][0]]=-planet_drange*1.2

                #if planet next to b has room move them
                elif (planets_by_pos[next_to_b][2] > (2*planet_drange)):
                    planets_delta[next_to_b]=-(groups[a][1][2]-planet_drange*2.5)
                    planets_delta[groups[a][1][0]]=+planet_drange*1.2

            #Three grouped planets or more
            xl=len(groups[a])        
            if xl >= 3:
                
                available = groups[a][0][1]
                for f in range(xl):
                    available += groups[a][f][2]
                need = (3*planet_drange)+(1.2*(xl-1)*planet_drange)
                leftover = available - need
                xa=groups[a][0][1]
                xb=groups[a][(xl-1)][2]
                
                #center
                if (xa > (need*.5)) & (xb > (need*.5)):
                    startA = xa - (need*.5)
                #position relative to next planets
                else:
                    startA=(leftover/(xa+xb))*xa
                    startB=(leftover/(xa+xb))*xb
            
                if available > need:
                    planets_delta[groups[a][0][0]]=startA-groups[a][0][1]+(1.5*planet_drange)
                    for f in range(xl-1):
                        planets_delta[groups[a][(f+1)][0]]=1.2*planet_drange+planets_delta[groups[a][f][0]]-groups[a][f][2]


        for e in range(len(keys)):
            i=planets_degut[keys[e]]

            #coordinates                            

            #if 22 < i < 27 it is asc,mc,dsc,ic (angles of chart)
            #put on special line (rplanet is range from outer ring)
            amin,bmin,cmin=0,0,0                

            if 22 < i < 27:
                rplanet = 40-cmin
            elif switch == 1:
                rplanet=74-amin
                switch = 0
            else:
                rplanet=94-bmin
                switch = 1            
            
            rtext=45

            offset = (int(self.houses_degree_ut[6]) / -1) + int(self.planets_degree_ut[i]+planets_delta[e])
            trueoffset = (int(self.houses_degree_ut[6]) / -1) + int(self.planets_degree_ut[i])
           
           
            planet_x = self.sliceToX( 0 , (r-rplanet) , offset ) + rplanet
            planet_y = self.sliceToY( 0 , (r-rplanet) , offset ) + rplanet

            scale=1
            #output planet            
            output = output + '<g transform="translate(-'+str(12*scale)+',-'+str(12*scale)+')"><g transform="scale('+str(scale)+')"><use x="' + str(planet_x*(1/scale)) + '" y="' + str(planet_y*(1/scale)) + '" xlink:href="#' + self.planets_asp[i]['name'] + '" /></g></g>\n'
            
        #make transit degut and display planets
        return output

    def makePatterns( self ):
        """
        * Stellium: At least four planets linked together in a series of continuous conjunctions.
        * Grand trine: Three trine aspects together.
        * Grand cross: Two pairs of opposing planets squared to each other.
        * T-Square: Two planets in opposition squared to a third. 
        * Yod: Two qunicunxes together joined by a sextile. 
        """
        conj = {} #0
        opp = {} #10
        sq = {} #5
        tr = {} #6
        qc = {} #9
        sext = {} #3
        for i in range(len(self.planets_asp)):
            a=self.planets_degree_ut[i]
            qc[i]={}
            sext[i]={}
            opp[i]={}
            sq[i]={}
            tr[i]={}
            conj[i]={}
            #skip some points
            n = self.planets_asp[i]['name']
            if n == 'earth' or n == 'true node' or n == 'osc. apogee' or n == 'intp. apogee' or n == 'intp. perigee':
                continue
            if n == 'Dsc' or n == 'Ic':
                continue
            for j in range(len(self.planets_asp)):
                #skip some points
                n = self.planets_asp[j]['name']
                if n == 'earth' or n == 'true node' or n == 'osc. apogee' or n == 'intp. apogee' or n == 'intp. perigee':
                    continue    
                if n == 'Dsc' or n == 'Ic':
                    continue
                b=self.planets_degree_ut[j]
                delta=float(self.degreeDiff(a,b))
                #check for opposition
                xa = float(self.aspects[10]['degree']) - float(self.aspects[10]['orb'])
                xb = float(self.aspects[10]['degree']) + float(self.aspects[10]['orb'])
                if( xa <= delta <= xb ):
                    opp[i][j]=True    
                #check for conjunction
                xa = float(self.aspects[0]['degree']) - float(self.aspects[0]['orb'])
                xb = float(self.aspects[0]['degree']) + float(self.aspects[0]['orb'])
                if( xa <= delta <= xb ):
                    conj[i][j]=True                    
                #check for squares
                xa = float(self.aspects[5]['degree']) - float(self.aspects[5]['orb'])
                xb = float(self.aspects[5]['degree']) + float(self.aspects[5]['orb'])
                if( xa <= delta <= xb ):
                    sq[i][j]=True            
                #check for qunicunxes
                xa = float(self.aspects[9]['degree']) - float(self.aspects[9]['orb'])
                xb = float(self.aspects[9]['degree']) + float(self.aspects[9]['orb'])
                if( xa <= delta <= xb ):
                    qc[i][j]=True
                #check for sextiles
                xa = float(self.aspects[3]['degree']) - float(self.aspects[3]['orb'])
                xb = float(self.aspects[3]['degree']) + float(self.aspects[3]['orb'])
                if( xa <= delta <= xb ):
                    sext[i][j]=True
                            
        yot={}
        #check for double qunicunxes
        for k,v in qc.items():
            if len(qc[k]) >= 2:
                #check for sextile
                for l,w in qc[k].items():
                    for m,x in qc[k].items():
                        if m in sext[l]:
                            if l > m:
                                yot['%s,%s,%s' % (k,m,l)] = [k,m,l]
                            else:
                                yot['%s,%s,%s' % (k,l,m)] = [k,l,m]
        tsquare={}
        #check for opposition
        for k,v in opp.items():
            if len(opp[k]) >= 1:
                #check for square
                for l,w in opp[k].items():
                        for a,b in sq.items():
                            if k in sq[a] and l in sq[a]:
                                #print 'got tsquare %s %s %s' % (a,k,l)
                                if k > l:
                                    tsquare['%s,%s,%s' % (a,l,k)] = '%s => %s, %s' % (
                                        self.planets_asp[a]['label'],self.planets_asp[l]['label'],self.planets_asp[k]['label'])
                                else:
                                    tsquare['%s,%s,%s' % (a,k,l)] = '%s => %s, %s' % (
                                        self.planets_asp[a]['label'],self.planets_asp[k]['label'],self.planets_asp[l]['label'])
        stellium={}
        #check for 4 continuous conjunctions    
        for k,v in conj.items():
            if len(conj[k]) >= 1:
                #first conjunction
                for l,m in conj[k].items():
                    if len(conj[l]) >= 1:
                        for n,o in conj[l].items():
                            #skip 1st conj
                            if n == k:
                                continue
                            if len(conj[n]) >= 1:
                                #third conjunction
                                for p,q in conj[n].items():
                                    #skip first and second conj
                                    if p == k or p == n:
                                        continue
                                    if len(conj[p]) >= 1:                                        
                                        #fourth conjunction
                                        for r,s in conj[p].items():
                                            #skip conj 1,2,3
                                            if r == k or r == n or r == p:
                                                continue
                                            
                                            l=[k,n,p,r]
                                            l.sort()
                                            stellium['%s %s %s %s' % (l[0],l[1],l[2],l[3])]='%s %s %s %s' % (
                                                self.planets_asp[l[0]]['label'],self.planets_asp[l[1]]['label'],
                                                self.planets_asp[l[2]]['label'],self.planets_asp[l[3]]['label'])
        #print yots
        out='<g transform="translate(-30,380)">'
        if len(yot) >= 1:
            y=0
            for k,v in yot.items():
                out += '<text y="%s" style="fill:%s; font-size: 12px;">%s</text>\n' % (y,self.colors['paper_0'],("Yot"))
                
                #first planet symbol
                out += '<g transform="translate(20,%s)">' % (y)
                out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
                    self.planets_asp[yot[k][0]]['name'])
                
                #second planet symbol
                out += '<g transform="translate(30,%s)">'  % (y)
                out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
                    self.planets_asp[yot[k][1]]['name'])

                #third planet symbol
                out += '<g transform="translate(40,%s)">'  % (y)
                out += '<use transform="scale(0.4)" x="0" y="-20" xlink:href="#%s" /></g>\n' % (
                    self.planets_asp[yot[k][2]]['name'])
                
                y=y+14
        #finalize
        out += '</g>'        
        #return out
        return ''
    
    def makeAspects( self , r , ar ):
        out=""
        for i in range(len(self.planets_asp)):
            start = self.planets_degree_ut[i]
            for x in range(i):
                end=self.planets_degree_ut[x]
                diff = float(self.degreeDiff(start,end))
                #loop variable_orbs
                if (self.planets_asp[i]['visible'] == 1) and (self.planets_asp[x]['visible'] == 1):
                    for z in range(len(self.aspects)):
                        variable_orb = float(self.aspects[z]['orb'])
                        axes = [12, 13, 14, 15]
                        if self.planets_asp[i]['id'] in axes  or self.planets_asp[x]['id'] in axes:
                            # self.orb 
                            variable_orb = 1
                        if    ( float(self.aspects[z]['degree']) - variable_orb)  <= diff <= ( float(self.aspects[z]['degree']) + variable_orb):
                            #check if we want to display this aspect
                            if self.aspects[z]['visible'] == 1:                    
                                out = out + self.drawAspect(r, ar, self.planets_degree_ut[i], self.planets_degree_ut[x], self.colors["aspect_%s" %(self.aspects[z]['degree'])] )
        
        return out
    

    def makeAspectGrid( self , r ):
        out=""
        style='stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none' % (self.colors['paper_0'])
        xindent=380
        yindent=468
        box=14
        revr = list(range(len(self.planets_asp)))
        revr.reverse()
        for a in revr:
            if self.planets_asp[a]['visible'] == 1:
                start=self.planets_degree_ut[a]
                #first planet 
                out = out + '<rect x="'+str(xindent)+'" y="'+str(yindent)+'" width="'+str(box)+'" height="'+str(box)+'" style="'+style+'"/>\n'
                out = out + '<use transform="scale(0.4)" x="'+str((xindent+2)*2.5)+'" y="'+str((yindent+1)*2.5)+'" xlink:href="#'+self.planets_asp[a]['name']+'" />\n'
                xindent = xindent + box
                yindent = yindent - box
                revr2=list(range(a))
                revr2.reverse()
                xorb=xindent
                yorb=yindent + box
                for b in revr2:
                    if self.planets_asp[b]['visible'] == 1:
                        end = self.planets_degree_ut[b]
                        diff = self.degreeDiff(start,end)
                        out = out + '<rect x="'+str(xorb)+'" y="'+str(yorb)+'" width="'+str(box)+'" height="'+str(box)+'" style="'+style+'"/>\n'
                        xorb = xorb+box
                        for z in range(len(self.aspects)):
                            variable_orb = float(self.aspects[z]['orb'])
                            axes = [12, 13, 14, 15]
                            if self.planets_asp[a]['id'] in axes  or self.planets_asp[b]['id'] in axes:
                            # self.orb 
                                variable_orb = 1
                            if    (float(self.aspects[z]['degree']) - variable_orb) <= diff <= (float(self.aspects[z]['degree']) + variable_orb) and self.aspects[z]['visible'] == 1:
                                    out = out + '<use  x="'+str(xorb-box+1)+'" y="'+str(yorb+1)+'" xlink:href="#orb'+str(self.aspects[z]['degree'])+'" />\n'
        return out

    def makeElements( self , r ):
        total = self.fire + self.earth + self.air + self.water
        pf = int(round(100*self.fire/total))
        pe = int(round(100*self.earth/total))
        pa = int(round(100*self.air/total))
        pw = int(round(100*self.water/total))
        out = '<g transform="translate(-30,79)">\n'
        out = out + '<text y="0" style="fill:#ff6600; font-size: 10px;">'+self.label['fire']+'  '+str(pf)+'%</text>\n'
        out = out + '<text y="12" style="fill:#6a2d04; font-size: 10px;">'+self.label['earth']+' '+str(pe)+'%</text>\n'
        out = out + '<text y="24" style="fill:#6f76d1; font-size: 10px;">'+self.label['air']+'   '+str(pa)+'%</text>\n'
        out = out + '<text y="36" style="fill:#630e73; font-size: 10px;">'+self.label['water']+' '+str(pw)+'%</text>\n'        
        out = out + '</g>\n'
        return out
        
    def makePlanetGrid( self ):
        out = '<g transform="translate(510,-40)">'
        #loop over all planets
        li = 10
        offset = 0
        for i in range(len(self.planets_asp)):
            if i == 27:
                li = 10
                offset = -120
            if self.planets_asp[i]['visible'] == 1:
                #start of line                
                out = out + '<g transform="translate(%s,%s)">' % (offset,li)
                #planet text
                out = out + '<text text-anchor="end" style="fill:%s; font-size: 10px;">%s</text>' % (self.colors['paper_0'],self.planets_asp[i]['label'])
                #planet symbol
                out = out + '<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#'+self.planets_asp[i]['name']+'" /></g>'                                
                #planet degree                
                out = out + '<text text-anchor="start" x="19" style="fill:%s; font-size: 10px;">%s</text>' % (self.colors['paper_0'],self.dec2deg(self.planets_degree[i]))
                #zodiac
                out = out + '<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#'+self.zodiac[self.planets_sign[i]]+'" /></g>'                
                #planet retrograde
                if self.planets_retrograde[i]:
                    out = out + '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'                

                #end of line
                out = out + '</g>\n'
                #offset between lines
                li = li + 14    
        
        out = out + '</g>\n'
        return out
    
    def makeHousesGrid( self ):
        out = '<g transform="translate(610,-40)">'
        li=10
        for i in range(12):
            if i < 9:
                cusp = '&#160;&#160;'+str(i+1)
            else:
                cusp = str(i+1)
            out += '<g transform="translate(0,'+str(li)+')">'
            out += '<text text-anchor="end" x="40" style="fill:%s; font-size: 10px;">%s %s:</text>' % (self.colors['paper_0'],self.label['cusp'],cusp)            
            out += '<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#'+self.zodiac[self.houses_sign[i]]+'" /></g>'
            out += '<text x="53" style="fill:%s; font-size: 10px;"> %s</text>' % (self.colors['paper_0'],self.dec2deg(self.houses_degree[i]))
            out += '</g>\n'
            li = li + 14
        out += '</g>\n'
        return out

#debug print function
def dprint(str):
    if DEBUG:
        print('%s' % str)






if __name__ == "__main__":
    import kerykeion as kr

    # Generate the SVG
    kanye = kr.Calculator("Kanye", 1977, 6, 8, 8, 45, "Atlanta", nat="USA")
    kanyeSVG = MakeInstance(kanye)
    kanyeSVG.set_dir = os.path.expanduser("~")
    kanyeSVG.makeSVG() 