from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item

class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `engine` is the scope this action is being performed in.

        `entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")

class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            if self.target_actor != None:
                if not self.target_actor.fighter.is_invul:
                    self.item.consumable.activate(self)
                else:
                    self.engine.message_log.add_message(
                        self.target_actor().name.capitalize() + " dodges the attack", color.white
                )

class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)

class WaitAction(Action):
    def perform(self) -> None:
        self.entity.fighter.restore_stam(1)
        pass

class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor("down")
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        elif (self.entity.x, self.entity.y) == self.engine.game_map.upstairs_location:
            self.engine.game_world.generate_floor("up")
            self.engine.message_log.add_message(
                "You ascend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")

class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)
        self.entity.inventory.drop(self.item)

class ToggleTwoHand(Action):
    def perform(self) -> None:
        self.entity.fighter.is_two_hand = not self.entity.fighter.is_two_hand

class ToggleBlock(Action):
    def perform(self) -> None:
        self.entity.fighter.is_blocking = not self.entity.fighter.is_blocking

class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)
        self.dx = dx
        self.dy = dy
        print(str(dx)+", "+str(dy))

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        if self.entity.fighter.stam < self.entity.fighter.stam_cost:
            self.engine.message_log.add_message(
                self.entity.name.capitalize() + " swings, exhausted, missing the target", color.white
            )
            self.entity.fighter.restore_stam(1)

        elif target.fighter.is_invul:
            self.entity.fighter.take_stam_atk()
            self.engine.message_log.add_message(
                target.name.capitalize() + " dodges the attack!", color.white
            )

        else:            
            damage = self.entity.fighter.power - target.fighter.defense

            self.entity.fighter.take_stam_atk()

            attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
            if self.entity is self.engine.player:
                attack_color = color.player_atk
            else:
                attack_color = color.enemy_atk
            if damage > 0:
                self.engine.message_log.add_message(
                    f"{attack_desc} for {damage} hit points.", attack_color
                )
                target.fighter.hp -= damage
            else:
                self.engine.message_log.add_message(
                    f"{attack_desc} but does no damage.", attack_color
                )


class MeleeActionHeavy(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        if self.entity.fighter.stam < round(self.entity.fighter.stam_cost * 1.6):
            self.engine.message_log.add_message(
                self.entity.name.capitalize() + " swings, exhausted, missing the target", color.white
            )
            self.entity.fighter.restore_stam(1)
        
        elif target.fighter.is_invul:
            self.entity.fighter.take_stam_atk()
            self.engine.message_log.add_message(
                target.name.capitalize() + " dodges the attack!", color.white
            )

        else:            
            damage = round(self.entity.fighter.power*1.6) - target.fighter.defense

            self.entity.fighter.take_stam(round(self.entity.fighter.stam_cost*1.5))

            attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
            if self.entity is self.engine.player:
                attack_color = color.player_atk
            else:
                attack_color = color.enemy_atk
            if damage > 0:
                self.engine.message_log.add_message(
                    f"{attack_desc} for {damage} hit points.", attack_color
                )
                target.fighter.hp -= damage
            else:
                self.engine.message_log.add_message(
                    f"{attack_desc} but does no damage.", attack_color
                )

class DodgeAction(ActionWithDirection):
    def perform(self) -> None:
        if self.entity.fighter.stam < 2:
            self.engine.message_log.add_message(
                self.entity.name.capitalize() + " dives out of the way but fails", color.white
            )

        else:   
            dest_x, dest_y = self.dest_xy
            self.entity.fighter.is_invul = not self.entity.fighter.is_invul
            if not self.engine.game_map.in_bounds(dest_x, dest_y):
                # Destination is out of bounds.
                raise exceptions.Impossible("That way is blocked by the world map.")
            if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
                # Destination is blocked by a tile.
                raise exceptions.Impossible("That way is blocked by a wall.")
            if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
                # Destination is blocked by an entity.
                dest_x += self.dx
                dest_y += self.dy
                self.dx *= 2
                self.dy *= 2
                if self.engine.game_map.in_bounds(dest_x, dest_y) and self.engine.game_map.tiles["walkable"][dest_x, dest_y] and not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
                    print(str(self.engine.game_map.in_bounds(dest_x, dest_y))+str(self.engine.game_map.tiles["walkable"][dest_x, dest_y])+str(not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)))
                else:
                    print(str(self.engine.game_map.in_bounds(dest_x, dest_y))+str(self.engine.game_map.tiles["walkable"][dest_x, dest_y])+str(not self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)))
                    raise exceptions.Impossible("That way is blocked by a character.")
            self.engine.message_log.add_message(
                self.entity.name.capitalize() + " dodges!", color.white
            )
            self.entity.move(self.dx, self.dy)
            self.entity.fighter.take_stam(2)


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")
        self.entity.move(self.dx, self.dy)
        self.entity.fighter.restore_stam(1)


class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()

        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()