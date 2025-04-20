# Dialogue Condition Types

This document outlines the different condition types available for dialogue options in the game.

## Item Condition Types

When creating dialogue options that require the player to have specific items, you can use the following condition types:

### required_items
Checks if the item exists in the player's main inventory only.

```yaml
conditions:
  required_items: ["police_badge", "notebook"]
```

### worn_items
Checks if the item is currently equipped/worn by the player. This is useful for items that NPCs need to visibly see on the player.

```yaml
conditions:
  worn_items: ["police_badge", "detective_coat"]
```

### required_items_any_inventory
Checks if the item exists anywhere in the player's possession - including main inventory, worn items, and containers.

```yaml
conditions:
  required_items_any_inventory: ["mysterious_key", "torn_photograph"]
```

### any_of
Allows for complex condition checking where any of the specified conditions can be true:

```yaml
conditions:
  any_of:
    - required_items: ["police_badge"]
    - worn_items: ["police_badge"]
    - required_items_any_inventory: ["police_badge"]
```

## Other Condition Types

### required_skills
Checks if the player has the required skill levels:

```yaml
conditions:
  required_skills:
    perception: 8
    logic: 5
```

### required_quests
Checks the status of specific quests:

```yaml
conditions:
  required_quests:
    "main_investigation": "InProgress"
    "missing_locket": "Completed"
```

### quest_objective_completed
Checks if a specific quest objective has been completed:

```yaml
conditions:
  quest_objective_completed:
    quest_id: "main_investigation"
    objective_id: "initial_investigation"
```

### npc_relationship_value
Checks if the player's relationship with a specific NPC is at or above a certain value:

```yaml
conditions:
  npc_relationship_value:
    npc_id: "guard_martinez"
    min_value: 70
```

## Combining Conditions

You can combine multiple condition types to create complex requirements:

```yaml
conditions:
  any_of:
    - required_items: ["police_badge"]
    - worn_items: ["police_badge"]
  required_skills:
    authority: 8
  required_quests:
    "main_investigation": "InProgress"
```

In this example, the player must have either the police badge in their inventory OR be wearing it, AND have an authority skill of at least 8, AND have the main investigation quest in progress. 