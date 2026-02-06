from __future__ import annotations
from .types import Command, Entity, LinkedLocation

class PlannerError(Exception):
    pass

class Planner:
    @classmethod
    def default(cls) -> Planner:
        return cls()

    def plan(self, entities: list[Entity], linked_locs: dict[int, LinkedLocation]) -> list[Command]:
        plan: list[Command] = []
        current_pos: str | None = None
        
        actions = [(i, e) for i, e in enumerate(entities) if e.type == "ACT"]
        
        if not actions:
            locs = [l for i, l in linked_locs.items()]
            if locs:
                plan.append(Command(cmd="GO", to=locs[0].id))
            return plan

        for idx_in_list, (ent_idx, act_ent) in enumerate(actions):
            cmd_type = act_ent.text
            
            context_locs = []
            for i in range(max(0, ent_idx - 3), min(len(entities), ent_idx + 4)):
                if i in linked_locs:
                    context_locs.append((entities[i].type, linked_locs[i]))

            loc_from = next((l for t, l in context_locs if t == "LOC_FROM"), None)
            loc_to = next((l for t, l in context_locs if t == "LOC_TO"), None)
            loc_any = next((l for t, l in context_locs if t == "LOC"), None)

            try:
                if cmd_type in ("GO", "RETURN"):
                    target = loc_to or loc_any
                    if target:
                        plan.append(Command(cmd="GO", to=target.id))
                        current_pos = target.id
                    elif cmd_type == "RETURN":
                        plan.append(Command(cmd="GO", to="CHARGE"))
                        current_pos = "CHARGE"

                elif cmd_type == "PICK":
                    target = loc_any or loc_from
                    if target and target.id != current_pos:
                        plan.append(Command(cmd="GO", to=target.id))
                        current_pos = target.id
                    plan.append(Command(cmd="PICK"))

                elif cmd_type == "DROP":
                    target = loc_any or loc_to
                    if target and target.id != current_pos:
                        plan.append(Command(cmd="GO", to=target.id))
                        current_pos = target.id
                    plan.append(Command(cmd="DROP"))

                elif cmd_type == "DELIVER":
                    if loc_from:
                        plan.append(Command(cmd="GO", to=loc_from.id))
                        current_pos = loc_from.id
                    plan.append(Command(cmd="PICK"))
                    
                    target = loc_to or loc_any
                    if target:
                        plan.append(Command(cmd="GO", to=target.id))
                        plan.append(Command(cmd="DROP"))
                        current_pos = target.id
            except Exception as e:
                raise PlannerError(f"Ошибка при планировании {cmd_type}: {str(e)}")

        return self._optimize(plan)

    def _optimize(self, plan: list[Command]) -> list[Command]:
        optimized = []
        last_to = None
        for cmd in plan:
            if cmd.cmd == "GO":
                if cmd.to == last_to: 
                    continue
                last_to = cmd.to
            optimized.append(cmd)
        return optimized