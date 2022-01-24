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
        self.max_hp = hp
        self._hp = hp
        self.max_stam = stam
        self._stam = stam
        self.base_defense = base_defense
        self.base_power = base_power
        self.stam_cost = base_cost

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
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0
