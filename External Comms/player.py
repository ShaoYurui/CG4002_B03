import json
import os
import sys
import random as random
import time
import tkinter as tk
from _socket import SHUT_RDWR
import socket
import threading
import base64
import traceback
from multiprocessing import Queue
from multiprocessing import Pipe
from queue import Empty
from timeit import default_timer as timer

"""
class player(threading.Thread):

    def __init__(self, player_to_eval_conn):
        self.max_grenades           = 2
        self.max_shields            = 3
        self.bullet_hp              = 10
        self.grenade_hp             = 30
        self.shield_max_time        = 10
        self.shield_health_max      = 30
        self.magazine_size          = 6
        self.max_hp                 = 100
        self.max_shield_respawn     = 10

        self.hp             = self.max_hp
        self.action         = 'none'
        self.bullets        = self.magazine_size
        self.grenades       = self.max_grenades
        self.shield_time    = 0
        self.shield_health  = 0
        self.num_shield     = self.max_shields
        self.num_deaths     = 0

        self.shield_activated = False
        self.shield_activate_time = 0

        self.shield_respawn_cooldown = False
        self.shield_respawn_starttime = 0
        self.shield_respawn_time = 0
        
        self.playerstate = None

        self.player_to_eval_conn = player_to_eval_conn

        threading.Thread.__init__(self)


    def get_dict (self):
        this_player = dict()
        this_player['hp']               = self.hp
        this_player['action']           = self.action
        this_player['bullets']          = self.bullets
        this_player['grenades']         = self.grenades
        this_player['shield_time']      = self.shield_time
        this_player['shield_health']    = self.shield_health
        this_player['num_deaths']       = self.num_deaths
        this_player['num_shield']       = self.num_shield
        
        return this_player
    
    def life_respawn(self):
        self.hp             = self.max_hp
        self.bullets        = self.magazine_size
        self.grenades       = self.max_grenades
        self.shield_time    = 0
        self.shield_health  = 0
        self.num_shield     = self.max_shields
        self.num_deaths     = self.num_deaths + 1

        self.shield_activated = False
        self.shield_activate_time = 0

        self.shield_respawn_cooldown = False
        self.shield_respawn_starttime = 0
        self.shield_respawn_time = 0
        
        self.playerstate = None

        return
    
    def perform_shoot(self):

        self.action = "shoot"
        
        # Execute only if magazine is not empty
        if (self.bullets > 0):
            self.bullets = self.bullets - 1
        
        self.playerstate = self.get_dict()
        return
    
    def perform_grenade(self):

        self.action = "grenade"

        # Execute only if there are grenades left
        if (self.grenades > 0):
            self.grenades = self.grenades - 1
        
        self.playerstate = self.get_dict()
        return
    
    def perform_shield(self):

        self.action = "shield"

        # Execute only if there are shields left and no shield is active
        if ((self.num_shield > 0) and (self.shield_respawn_cooldown == False)):
            self.num_shield = self.num_shield - 1
            self.shield_time = self.shield_max_time
            self.shield_health = self.shield_health_max
            self.shield_activate_time = timer()
        
        self.playerstate = self.get_dict()
        return
    
    def perform_reload(self):

        self.action = "reload"

        # Execute only if magazine is empty
        if (self.bullets == 0):
            self.bullets = self.magazine_size
        
        self.playerstate = self.get_dict()
        return
    
    
    def bullet_hit(self):

        self.action = "none"
        
        # Case 1 : Shield is activated
        if self.shield_activated == True:
            # Case 1.1 : This hit destroys the shield
            if self.shield_health == 10:
                self.shield_health = 0
                self.shield_activated = False
                self.shield_activate_time = None
                self.num_shield = self.num_shield - 1
            
            # Case 1.2 : This hit does not destroy the shield
            elif self.shield_health > 10:
                self.shield_health = self.shield_health - 10
        
        # Case 2 : Shield is not activated
        elif self.shield_activated == False:
            # Case 2.1 : This hit kills the player
            if self.hp <= 10:
                self.hp = 0
                self.life_respawn()
            # Case 2.2 : This hit does not kill the player
            elif self.hp > 10:
                self.hp = self.hp - 10

        self.playerstate = self.get_dict()
        return
    
    def grenade_hit(self):

        self.action = "none"
        
        # Case 1 : Shield is activated
        if self.shield_activated == True:
            # Case 1.1 : This hit destroys the shield but does not harm the player
            if self.shield_health == 30:
                self.shield_health = 0
                self.shield_activated = False
                self.shield_activate_time = None
                self.num_shield = self.num_shield - 1

            # Case 1.2 : This hit destroys shield and harms the player
            elif self.shield_health < 30:
                self.shield_health = 0
                self.shield_activated = False
                self.shield_activate_time = None
                self.num_shield = self.num_shield - 1

                hp_damage = 30 - self.shield_health

                # Case 1.2.1 : The HP damage kills the player
                if self.hp <= hp_damage:
                    self.hp = 0
                    self.life_respawn()
                
                # Case 1.2.2 : The HP damage does not kill the player
                elif self.hp > hp_damage:
                    self.hp = self.hp - hp_damage
        
        # Case 2 : Shield is not activated
        elif self.shield_activated == False:
            # Case 2.1 : This hit kills the player
            if self.hp <= 30:
                self.life_respawn()
            # Case 2.2 : This hit does not kill the player
            elif self.hp > 30:
                self.hp = self.hp - 30

        self.playerstate = self.get_dict()
        return

    def update_shield_timings(self):
        
        if ((self.shield_activated == False) and (self.shield_time == 0)):
            return
        
        current_time = timer()
        self.shield_time = self.shield_max_time - int(current_time - self.shield_activate_time)

        if self.shield_time <= 0:
            self.shield_activated = False
            self.shield_activate_time = None
            self.shield_respawn_cooldown = True
            self.shield_respawn_starttime = timer()
            self.shield_respawn_time = 10
            self.shield_time = 0
        
        self.playerstate = self.get_dict()
        return
    
    def update_respawn_timings(self):
        
        if self.shield_respawn_cooldown == False:
            return
        
        # Only Executed if shield is respawning
        current_time = timer()
        self.shield_respawn_time = self.max_shield_respawn - int(current_time - self.shield_respawn_starttime)

        if self.shield_respawn_time <= 0:
            self.shield_respawn_cooldown = False

        self.playerstate = self.get_dict()
        return


    def run(self):
        while True:
            self.update_shield_timings()
            self.update_respawn_timings()

            try: 
                command = self.player_to_eval_conn.recv()
                print("From Player: Performing Action")

                if command == "perform_shoot":
                    self.perform_shoot()
                elif command == "perform_grenade":
                    self.perform_grenade()
                elif command == "perform_shield":
                    self.perform_shield()
                elif command == "perform_reload":
                    self.perform_reload()
                elif command == "bullet_hit":
                    self.bullet_hit()
                elif command == "grenade_hit":
                    self.grenade_hit()
                
                current_playerstate = self.playerstate
                print(current_playerstate)
                self.player_to_eval_conn.send(current_playerstate)
                print("From Player: Action Complete")


            except Empty:
                continue
"""

class player(threading.Thread):

    def __init__(self, eval_to_player_queue, player_to_eval_queue):
        self.max_grenades           = 2
        self.max_shields            = 3
        self.bullet_hp              = 10
        self.grenade_hp             = 30
        self.shield_max_time        = 10
        self.shield_health_max      = 30
        self.magazine_size          = 6
        self.max_hp                 = 100

        self.hp             = self.max_hp
        self.action         = 'none'
        self.bullets        = self.magazine_size
        self.grenades       = self.max_grenades
        self.shield_time    = 0
        self.shield_health  = 0
        self.num_shield     = self.max_shields
        self.num_deaths     = 0

        self.shield_activated = False
        self.shield_activate_time = 0
        
        self.playerstate = None

        self.clock_offset = 0
        self.offset_calculated = False

        self.eval_to_player_queue = eval_to_player_queue
        self.player_to_eval_queue = player_to_eval_queue

        threading.Thread.__init__(self)


    def get_dict (self):
        _player = dict()
        _player['hp']               = self.hp
        _player['action']           = self.action
        _player['bullets']          = self.bullets
        _player['grenades']         = self.grenades
        _player['shield_time']      = self.shield_time
        _player['shield_health']    = self.shield_health
        _player['num_deaths']       = self.num_deaths
        _player['num_shield']       = self.num_shield
        
        return _player
    
    def life_respawn(self):
        self.hp             = self.max_hp
        self.bullets        = self.magazine_size
        self.grenades       = self.max_grenades
        self.shield_time    = 0
        self.shield_health  = 0
        self.num_shield     = self.max_shields
        self.num_deaths     = self.num_deaths + 1

        self.shield_activated = False
        self.shield_activate_time = 0

        self.shield_respawn_cooldown = False
        self.shield_respawn_starttime = 0
        self.shield_respawn_time = 0
        
        self.playerstate = None

        return
    
    def perform_shoot(self):

        self.action = "shoot"
        
        # Execute only if magazine is not empty
        if (self.bullets > 0):
            self.bullets = self.bullets - 1
        
        self.playerstate = self.get_dict()
        return
    
    def perform_grenade(self):

        self.action = "grenade"

        # Execute only if there are grenades left
        if (self.grenades > 0):
            self.grenades = self.grenades - 1
        
        self.playerstate = self.get_dict()
        return
    
    def perform_shield(self):

        self.action = "shield"

        # Execute only if there are shields left and no shield is active and it's not under cooldown
        if ((self.num_shield > 0) and (self.shield_time == 0) and (self.shield_activated == False)):
            self.num_shield = self.num_shield - 1
            self.shield_activated = True
            self.shield_time = self.shield_max_time
            self.shield_health = self.shield_health_max
            self.shield_activate_time = timer()
        
        self.playerstate = self.get_dict()
        print(self.playerstate)
        return
    
    def perform_reload(self):

        self.action = "reload"

        # Execute only if magazine is empty
        if (self.bullets == 0):
            self.bullets = self.magazine_size
        
        self.playerstate = self.get_dict()
        return
    
    
    def bullet_hit(self):

        self.action = "none"
        
        # Case 1 : Shield is activated
        if self.shield_activated == True:
            # Case 1.1 : This hit destroys the shield
            if self.shield_health == 10:
                self.shield_health = 30
                self.shield_activated = False
                self.shield_activate_time = 0
                self.num_shield = self.num_shield - 1
            
            # Case 1.2 : This hit does not destroy the shield
            elif self.shield_health > 10:
                self.shield_health = self.shield_health - 10
        
        # Case 2 : Shield is not activated
        elif self.shield_activated == False:
            # Case 2.1 : This hit kills the player
            if self.hp <= 10:
                self.hp = 0
                self.life_respawn()
            # Case 2.2 : This hit does not kill the player
            elif self.hp > 10:
                self.hp = self.hp - 10

        self.playerstate = self.get_dict()
        return
    
    def grenade_hit(self):

        self.action = "none"
        
        # Case 1 : Shield is activated
        if self.shield_activated == True:
            # Case 1.1 : This hit destroys the shield but does not harm the player
            if self.shield_health == 30:
                self.shield_health = 30
                self.shield_activated = False
                self.shield_activate_time = 0
                self.num_shield = self.num_shield - 1

            # Case 1.2 : This hit destroys shield and harms the player
            elif self.shield_health < 30:
                self.shield_health = 30
                self.shield_activated = False
                self.shield_activate_time = 0
                self.num_shield = self.num_shield - 1

                hp_damage = 30 - self.shield_health

                # Case 1.2.1 : The HP damage kills the player
                if self.hp <= hp_damage:
                    self.hp = 0
                    self.life_respawn()
                
                # Case 1.2.2 : The HP damage does not kill the player
                elif self.hp > hp_damage:
                    self.hp = self.hp - hp_damage
        
        # Case 2 : Shield is not activated
        elif self.shield_activated == False:
            # Case 2.1 : This hit kills the player
            if self.hp <= 30:
                self.life_respawn()
            # Case 2.2 : This hit does not kill the player
            elif self.hp > 30:
                self.hp = self.hp - 30

        self.playerstate = self.get_dict()
        return
    
    def no_apply(self):
        self.action = "none"
        self.playerstate = self.get_dict()
        return


    def update_shield_timings(self):
        
        if ((self.shield_activated == False) and (self.shield_time == 0)):
            return
        
        current_time = timer()
        self.shield_time = self.shield_max_time - (current_time - self.shield_activate_time) - self.clock_offset

        if self.shield_time <= 0:
            self.shield_activated = False
            self.shield_health = 0
            self.shield_activate_time = 0
            self.shield_respawn_cooldown = True
            self.shield_time = 0
        
        self.playerstate = self.get_dict()
        return
    
    """
    def update_respawn_timings(self):
        
        if self.shield_respawn_cooldown == False:
            return
        
        # Only Executed if shield is respawning
        current_time = timer()
        self.shield_respawn_time = self.max_shield_respawn - (current_time - self.shield_respawn_starttime)

        if self.shield_respawn_time <= 0:
            self.shield_respawn_cooldown = False

        self.playerstate = self.get_dict()
        return
    """


    def run(self):
        while True:
            self.update_shield_timings()
            # self.update_respawn_timings()

            try: 
                command = self.eval_to_player_queue.get()

                if command == "perform_shoot":
                    self.perform_shoot()
                elif command == "perform_grenade":
                    self.perform_grenade()
                elif command == "perform_shield":
                    self.perform_shield()
                elif command == "perform_reload":
                    self.perform_reload()
                elif command == "bullet_hit":
                    self.bullet_hit()
                elif command == "grenade_hit":
                    self.grenade_hit()
                elif command == "no_apply":
                    self.no_apply()
                elif command == "logout":
                    self.player_to_eval_queue.put("logout")
                    sys.exit()
                
                self.player_to_eval_queue.put(self.playerstate)

            except Empty:
                continue

            new_playerstate = self.eval_to_player_queue.get()
            # Obtain Clock offset to ensure error is not propagated
            self.clock_offset = self.clock_offset + (self.playerstate["shield_time"] - new_playerstate["shield_time"])
            # self.shield_activate_time = self.shield_activate_time - (self.playerstate["shield_time"] - new_playerstate["shield_time"])

            # Situation where shield is false negative
            if ((new_playerstate["action"] == "shield") and (self.playerstate["action"] != "shield")):
                self.shield_activated = True
            
            elif ((new_playerstate["action"] != "shield") and (self.playerstate["action"] == "shield")):
                if self.shield_time == self.shield_max_time:
                    self.shield_activated = False
            
            # Fixing Player State
            self.playerstate = new_playerstate
            self.hp             = self.playerstate["hp"]
            self.action         = self.playerstate["action"]
            self.bullets        = self.playerstate["bullets"]
            self.grenades       = self.playerstate["grenades"]
            self.shield_time    = self.playerstate["shield_time"]
            self.shield_health  = self.playerstate["shield_health"]
            self.num_shield     = self.playerstate["num_shield"]
            self.num_deaths     = self.playerstate["num_deaths"]            
    

        

        
        