from __future__ import annotations

from typing import TYPE_CHECKING
from components.base_component import BaseComponent
from render_order import RenderOrder
import color

if TYPE_CHECKING:
    from entity import Actor

class Fighter(BaseComponent):
    parent: Actor
    
    def __init__(self, hp: int, stam:int, base_defense: int, base_power: int, base_cost):
        '''
        Starting with having all states be base 5 and then we'll do different
        classes at a different time. Max level = 50, Soft-cap 25.
        '''
        self.gusto = 5
        self.stren = 5
        self.dex = 5
        self.know = 5
        self.fth = 5
        self.luck = 5 
        '''
        Factor level stats into stats.
        '''
        # FIXME This is so we have a copy of these initial variables
        self.hp_initial = hp
        self.stam_initial = stam
        self.def_initial = base_defense
        # remove later

        self.max_hp = hp + int(self.gusto*1.8)
        self._hp = self.max_hp
        self.max_stam = stam + int(self.stren+self.dex/2*1.8)
        self._stam = self.max_stam 
        self.base_defense = base_defense + int(self.stren*.4)
        self.base_power = base_power
        self.stam_cost = base_cost
        self.is_invul = False
        self.is_blocking = False
        self.is_two_hand = False

    @property
    def hp(self) -> int:    
        return self._hp
    
    @property
    def stam(self) -> int:    
        return self._stam

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @stam.setter
    def stam(self, value: int) -> None:
        self._stam = max(0, min(value, self.max_stam))

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die

        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE
        self.engine.message_log.add_message(death_message, death_message_color)
        self.engine.player.level.add_xp(self.parent.level.xp_given)
    
    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount

    def restore_stam(self, amount: int):
        if self.stam == self.max_stam:
            return
        
        new_stam_value = self.stam+amount
        print(str(new_stam_value))
        if new_stam_value > self.max_stam:
            new_stam_value = self.max_stam
        
        self.stam = new_stam_value
        return
        
          
    def take_stam(self, amount: int):
        self.stam = max(self.stam - amount, 0)

    def take_stam_atk(self):
        self.stam = max(self.stam - self.stam_cost, 0)    

    '''
    Handle resetting stats on level up
    '''
    def level_up_handler(self):
        self.max_hp = self.hp_initial + int(self.gusto*1.8)
        self.max_stam = self.stam_initial + int(self.stren+self.dex/2*1.8)
        self.base_defense = self.def_initial + int(self.stren*.4)

    @property
    def defense(self) -> int:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self) -> int:
        boost = 0
        for stat in self.parent.equipment.power_type:
            boost += stat * (1/self.parent.equipment.power_type)
            #FIXME add scaling percentages to above later
        if self.parent.equipment:
            return self.parent.equipment.power_bonus + int(boost)
        else:
            return boost
