from kerykeion.astrocore import Calculator
from kerykeion.utilities.kr_settings import aspects, colors, planets, axes_orbit
from swisseph import difdeg2n





class NatalAspects():
    
    def __init__(self, kr_object):
        self.user = kr_object
        
        if not hasattr(self.user, "sun"):
            print(f"Generating kerykeion object for {self.user.name}...")
            self.user.get_all()
    

    def asp_calc(self, point_one, point_two):
        """ 
        Calculates the aspects between the 2 points.
        Args: first point, second point. 
        """

        distance = abs(difdeg2n(point_one, point_two))
        diff = abs(point_one - point_two)

        if int(distance) <= aspects[0]['orb']:
            name = aspects[0]['name']
            aspect_degrees = aspects[0]['degree']
            color = colors['aspect_0']
            verdict = True
            aid = 0

        elif ( aspects[1]['degree'] - aspects[1]['orb']) <= int(distance) <= ( aspects[1]['degree'] + aspects[1]['orb']):
            name = aspects[1]['name']
            aspect_degrees = aspects[1]['degree']
            color = colors['aspect_30']
            verdict = True
            aid = 1

        elif ( aspects[2]['degree'] - aspects[2]['orb']) <= int(distance) <= ( aspects[2]['degree'] + aspects[2]['orb']):
            name = aspects[2]['name']
            aspect_degrees = aspects[2]['degree']
            color = colors['aspect_45']
            verdict = True
            aid = 2
        
        elif ( aspects[3]['degree'] - aspects[3]['orb']) <= int(distance) <= ( aspects[3]['degree'] + aspects[3]['orb']):
            name = aspects[3]['name']
            aspect_degrees = aspects[3]['degree']
            color = colors['aspect_60']
            verdict = True
            aid = 3
        
        elif ( aspects[4]['degree'] - aspects[4]['orb']) <= int(distance) <= ( aspects[4]['degree'] + aspects[4]['orb']):
            name = aspects[4]['name']
            aspect_degrees = aspects[4]['degree']
            color = colors['aspect_72']
            verdict = True
            aid = 4
        
        elif ( aspects[5]['degree'] - aspects[5]['orb']) <= int(distance) <= ( aspects[5]['degree'] + aspects[5]['orb']):
            name = aspects[5]['name']
            aspect_degrees = aspects[5]['degree']
            color = colors['aspect_90']
            verdict = True
            aid = 5

        elif ( aspects[6]['degree'] - aspects[6]['orb']) <= int(distance) <= ( aspects[6]['degree'] + aspects[6]['orb']):
            name = aspects[6]['name']
            aspect_degrees = aspects[6]['degree']
            color = colors['aspect_120']
            verdict = True
            aid = 6


        elif ( aspects[7]['degree'] - aspects[7]['orb']) <= int(distance) <= ( aspects[7]['degree'] + aspects[7]['orb']):
            name = aspects[7]['name']
            aspect_degrees = aspects[7]['degree']
            color = colors['aspect_135']
            verdict = True
            aid = 7
        
        elif ( aspects[8]['degree'] - aspects[8]['orb']) <= int(distance) <= ( aspects[8]['degree'] + aspects[8]['orb']):
            name = aspects[8]['name']
            aspect_degrees = aspects[8]['degree']
            color = colors['aspect_144']
            verdict = True
            aid = 8
        
        elif ( aspects[9]['degree'] - aspects[9]['orb']) <= int(distance) <= ( aspects[9]['degree'] + aspects[9]['orb']):
            name = aspects[9]['name']
            aspect_degrees = aspects[9]['degree']
            color = colors['aspect_150']
            verdict = True
            aid = 9


        elif ( aspects[10]['degree'] - aspects[10]['orb']) <= int(distance) <= ( aspects[10]['degree'] + aspects[10]['orb']):
            name = aspects[10]['name']
            aspect_degrees = aspects[10]['degree']
            color = colors['aspect_180']
            verdict = True
            aid = 10

        else:
            verdict = False
            name = None
            distance = 0
            aspect_degrees = 0
            color = None
            aid = None
            
        
        return verdict, name, distance - aspect_degrees, aspect_degrees, color, aid, diff
    
    def p_id_decoder(self, name):

        """ 
        Check if the name of the planet is the same in the settings and return
        the correct id for the planet.
        """
        str_name = str(name)
        for a in planets:
            if a['name'] == str_name:
                result = a['id']
                return result
                
    def get_all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        whitout repetitions.
        """
        

        point_list_tmp = self.user.planets_list + self.user.house_list


        #list of desired points names
        set_points_name = []
        for p in planets:
            if p['visible']:
                set_points_name.append(p['name'])
        
        self.point_list = []
        for l in point_list_tmp:
            if l['name'] in set_points_name:
                self.point_list.append(l)

        
        self.all_aspects_list = []

        for first in range(len(self.point_list)):
        #Generates the aspects list whitout repetitions
            for second in range(first + 1, len(self.point_list)):
                
                verdict, name, orbit, aspect_degrees, color, aid, diff = self.asp_calc(self.point_list[first]["abs_pos"],
                self.point_list[second]["abs_pos"])
                
                if verdict == True:
                    d_asp = { "p1_name": self.point_list[first]['name'],
                              "p1_abs_pos": self.point_list[first]['abs_pos'],
                              "p2_name": self.point_list[second]['name'],
                              "p2_abs_pos": self.point_list[second]['abs_pos'],
                              "aspect": name,
                              "orbit": orbit,
                              "aspect_degrees": aspect_degrees,
                              "color": color,
                              "aid": aid,
                              "diff": diff,
                              "p1": self.p_id_decoder(self.point_list[first]['name']),
                              "p2": self.p_id_decoder(self.point_list[second]['name'],)
                     }

                    self.all_aspects_list.append(d_asp)

        return self.all_aspects_list


   

    def get_aspects(self):
        """ 
        Filters the aspects list with the desired points, in this case
        the most important are hardcoded.
        Set the list with set_points and creating a list with the names
        or the numbers of the houses.
        """
            
        self.get_all_aspects()

        aspects_filtered = []
        for a in self.all_aspects_list:
            if aspects[a["aid"]]["visible"] == True:
                aspects_filtered.append(a)  



        axes_list = ["1", "10", "7", "4"]
        counter = 0

        aspects_list_subtract = []
        for a in aspects_filtered:
            counter += 1
            name_p1 = str(a['p1_name'])
            name_p2 = str(a['p2_name'])
            
            if name_p1 in axes_list:
                if abs(a['orbit']) >= axes_orbit:
                    aspects_filtered.remove(a)

            elif name_p2 in axes_list:
                if abs(a['orbit']) >= axes_orbit:
                    aspects_list_subtract.append(a)


        self.aspects = [item for item in aspects_filtered if item not in aspects_list_subtract]




        return self.aspects

if __name__ == "__main__":
    kanye = Calculator("Kanye", 1977, 6, 8, 8, 45, "Atlanta")
    kanye = Calculator("Jack", 1990, 6, 15, 13, 00, "Montichiari")
    kanye.get_all()
    natal = NatalAspects(kanye)
    natal.get_aspects()
    for a in natal.aspects:
        print(a['p1_name'], a['p2_name'], a['orbit'])
    
    
        